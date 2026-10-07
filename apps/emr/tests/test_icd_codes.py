"""ICD-10 codes: what may be stored, how the map table is loaded, how stored
codes are repaired.

Spec for the 2026-10-06 fix. Before it, a third of production's coded problems
carried a code no lab could bill — category headers, WHO ICD-10 codes and `?`
placeholders — because the map table had been filled from the wrong file and
nothing checked a code before storing it. Read `emr.icd_codes` first; several
assertions here are owner decisions rather than obvious truths:

  * a `?` placeholder is never assigned, and a stored one is BLANKED rather
    than given a letter (the seventh character depends on the visit);
  * the owner's recorded decision beats the map, and reaches new problems;
  * a billable code that is not the old table's pick is never touched, even
    when the map disagrees with it;
  * with no reference list on disk every check is off, not on.
"""
import json
from io import StringIO
from unittest import mock

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from emr import icd_codes
from emr.icd_codes import (
    assignable_icd10_for, explain_assignable, is_billable, is_legacy_pick,
    placeholder_pick_for, resolve_incoming_icd,
)
from emr.management.commands.repair_icd10_codes import classify
from emr.models import PatientMutationStamp, Problem, SnomedIcd10Map, UserProfile
from emr.tests.icd_fixtures import (
    CHOL, COUGH, DEPRESSION, DERM, FIT, HTN, MAP_HEADER, MAP_ROWS, RETIRED, SPRAIN,
    UNKNOWN, IcdFixtureMixin, bundled_map_text,
)


class IcdRuleTests(IcdFixtureMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.load_map_rows()

    # -- the reference ---------------------------------------------------

    def test_headers_who_codes_and_placeholders_are_not_billable(self):
        self.assertTrue(is_billable('E78.00'))
        self.assertFalse(is_billable('E78.0'))        # category header
        self.assertFalse(is_billable('R07.4'))        # WHO ICD-10, not ICD-10-CM
        self.assertFalse(is_billable('S93.409?'))     # placeholder
        self.assertFalse(is_billable(''))
        self.assertTrue(is_billable(' e78.00 '))      # compared trimmed, upper-cased

    def test_a_missing_reference_turns_the_checks_off_not_on(self):
        # The dangerous default would be "nothing is billable": every code a
        # client sends would be thrown away.
        with mock.patch.object(icd_codes, 'BILLABLE_FILE', '/nonexistent/billable.txt'):
            icd_codes.clear_caches()
            self.assertIsNone(icd_codes.billable_codes())
            self.assertTrue(is_billable('E78.0'))
            self.assertEqual(resolve_incoming_icd(CHOL, 'E78.0', current='', concept_changed=True), 'E78.0')
        icd_codes.clear_caches()

    # -- what the server assigns -------------------------------------------

    def test_the_unconditional_default_beats_a_conditional_row(self):
        self.assertEqual(assignable_icd10_for(HTN), 'I10')

    def test_a_placeholder_is_never_assigned(self):
        self.assertIsNone(assignable_icd10_for(SPRAIN))
        self.assertEqual(placeholder_pick_for(SPRAIN), 'S93.409?')
        self.assertIsNone(placeholder_pick_for(UNKNOWN))

    def test_a_recorded_decision_reaches_a_concept_the_map_cannot_code(self):
        # Until this fix decisions were applied once, to existing rows; every
        # "Fit and well" problem created afterwards was blank.
        self.assertFalse(SnomedIcd10Map.objects.filter(snomed_concept_id=FIT).exists())
        self.assertEqual(explain_assignable(FIT), ('Z00.00', 'decision', FIT))

    def test_a_recorded_decision_beats_the_map(self):
        self.write_decisions({DEPRESSION: 'F32.9'})
        self.assertEqual(assignable_icd10_for(DEPRESSION), 'F32.9')

    def test_a_decision_that_stopped_being_billable_is_ignored(self):
        self.write_decisions({DEPRESSION: 'F32'})
        self.assertEqual(assignable_icd10_for(DEPRESSION), 'F32.A')

    def test_a_retired_concept_takes_its_successors_code(self):
        self.assertEqual(explain_assignable(RETIRED), ('R05.9', 'successor', COUGH))

    def test_nothing_is_assigned_to_an_unknown_or_empty_concept(self):
        self.assertIsNone(assignable_icd10_for(UNKNOWN))
        self.assertIsNone(assignable_icd10_for(''))
        self.assertIsNone(assignable_icd10_for(None))

    # -- the old table's picks ---------------------------------------------

    def test_an_old_pick_is_legacy_only_when_the_map_offers_something_else(self):
        self.assertTrue(is_legacy_pick(DEPRESSION, 'F32.9'))
        self.assertFalse(is_legacy_pick(DEPRESSION, 'F32.A'))
        # DERM has no clean map row: replacing a plausible code with a blank
        # helps nobody, so the old pick stands.
        self.assertFalse(is_legacy_pick(DERM, 'L30.9'))

    def test_a_decision_for_the_old_pick_makes_it_a_choice_again(self):
        self.write_decisions({DEPRESSION: 'F32.9'})
        self.assertFalse(is_legacy_pick(DEPRESSION, 'F32.9'))

    # -- what happens to the code a client sent -----------------------------

    def test_a_deliberate_billable_code_is_stored_as_sent(self):
        self.assertEqual(resolve_incoming_icd(CHOL, 'K21.9', current='E78.00'), 'K21.9')

    def test_a_non_billable_code_on_a_new_problem_becomes_the_maps_code(self):
        self.assertEqual(resolve_incoming_icd(CHOL, 'E78.0', current='', concept_changed=True), 'E78.00')

    def test_a_non_billable_code_with_nothing_to_assign_is_blank(self):
        self.assertEqual(resolve_incoming_icd(UNKNOWN, 'M25.56', current='', concept_changed=True), '')
        self.assertEqual(resolve_incoming_icd(SPRAIN, 'S93.409?', current='', concept_changed=True), '')

    def test_a_stale_client_cannot_push_an_old_code_over_a_repaired_one(self):
        # Header echo, and the billable-but-legacy echo that a billable check
        # alone would wave through.
        self.assertEqual(resolve_incoming_icd(CHOL, 'E78.0', current='E78.00'), 'E78.00')
        self.assertEqual(resolve_incoming_icd(DEPRESSION, 'F32.9', current='F32.A'), 'F32.A')

    def test_an_empty_code_never_blanks_a_stored_one(self):
        self.assertEqual(resolve_incoming_icd(CHOL, '', current='E78.00'), 'E78.00')
        self.assertEqual(resolve_incoming_icd(CHOL, None, current='E78.00'), 'E78.00')

    def test_an_empty_code_on_an_uncoded_problem_is_assigned(self):
        self.assertEqual(resolve_incoming_icd(CHOL, '', current=''), 'E78.00')

    def test_a_concept_change_replaces_the_old_concepts_code(self):
        # The stored I10 belonged to hypertension. Kept, it would print beside
        # the cough's SNOMED code.
        self.assertEqual(resolve_incoming_icd(COUGH, '', current='I10', concept_changed=True), 'R05.9')
        self.assertEqual(resolve_incoming_icd(SPRAIN, '', current='I10', concept_changed=True), '')

    def test_a_replaced_code_is_logged_with_its_reason(self):
        with self.assertLogs('smallbrain.icd_guard', level='INFO') as logs:
            resolve_incoming_icd(CHOL, 'E78.0', current='', concept_changed=True, context={'endpoint': 'x'})
            resolve_incoming_icd(DEPRESSION, 'F32.9', current='F32.A')
        rows = [json.loads(line.split(':', 2)[2]) for line in logs.output]
        self.assertEqual([r['reason'] for r in rows], ['not_billable', 'legacy_pick'])
        self.assertEqual(rows[0]['stored'], 'E78.00')
        self.assertEqual(rows[0]['endpoint'], 'x')

    def test_an_accepted_code_logs_nothing(self):
        with self.assertNoLogs('smallbrain.icd_guard', level='INFO'):
            resolve_incoming_icd(CHOL, 'E78.00', current='')
            resolve_incoming_icd(CHOL, '', current='E78.00')


class LoadIcd10MapTests(IcdFixtureMixin, TestCase):
    def run_loader(self, *args, **kwargs):
        out = StringIO()
        kwargs.setdefault('mapfile', self.map_file)
        kwargs.setdefault('min_rows', 0)
        call_command('load_icd10_map', *args, stdout=out, **kwargs)
        return out.getvalue()

    def stale_row(self):
        # A WHO-map row of the kind the old loader let in.
        return SnomedIcd10Map.objects.create(
            snomed_concept_id=COUGH, map_group=1, map_priority=1, icd10_code='R05', map_advice='ALWAYS R05')

    def test_a_dry_run_writes_nothing(self):
        self.stale_row()
        output = self.run_loader()
        self.assertIn('Dry run', output)
        self.assertEqual(SnomedIcd10Map.objects.count(), 1)

    def test_apply_replaces_the_table_rather_than_adding_to_it(self):
        # The defect: the old command appended with ignore_conflicts, so a
        # reload could never remove a row. COUGH kept its WHO code beside the
        # real one and the pick fell to whichever was inserted first.
        self.stale_row()
        self.run_loader(apply=True)
        self.assertEqual(SnomedIcd10Map.objects.count(), len(MAP_ROWS))
        self.assertFalse(SnomedIcd10Map.objects.filter(icd10_code='R05').exists())
        self.assertEqual(SnomedIcd10Map.best_icd10_for(COUGH), 'R05.9')

    def test_a_second_run_has_nothing_to_do(self):
        self.run_loader(apply=True)
        self.assertIn('already matches', self.run_loader(apply=True))

    def test_a_raw_snomed_release_file_is_refused(self):
        raw = self._write('raw.txt', 'id\teffectiveTime\tactive\tmoduleId\trefsetId\n')
        with self.assertRaisesMessage(CommandError, 'not a bundled map file'):
            self.run_loader(mapfile=raw, apply=True)

    def test_a_tied_top_rank_is_refused(self):
        # Two first-priority unconditional rows: exactly what the WHO map and
        # the US map produced together.
        rows = MAP_ROWS + [(COUGH, 1, 1, 'R07.9', 'ALWAYS R07.9')]
        tied = self._write('tied.tsv', bundled_map_text(rows))
        self.stale_row()
        with self.assertRaisesMessage(CommandError, 'tied top rank'):
            self.run_loader(mapfile=tied, apply=True)
        self.assertEqual(SnomedIcd10Map.objects.count(), 1)

    def test_a_map_whose_picks_are_not_billable_is_refused(self):
        who = self._write('who.tsv', '# who\n' + MAP_HEADER + f'{COUGH}\t1\t1\tR05\tALWAYS R05\n')
        with self.assertRaisesMessage(CommandError, 'neither billable'):
            self.run_loader(mapfile=who, apply=True)
        self.assertEqual(SnomedIcd10Map.objects.count(), 0)

    def test_a_truncated_file_cannot_empty_the_table(self):
        self.stale_row()
        with self.assertRaisesMessage(CommandError, 'refusing to replace'):
            self.run_loader(apply=True, min_rows=100000)
        self.assertEqual(SnomedIcd10Map.objects.count(), 1)

    def test_a_missing_billable_list_refuses_to_load(self):
        with mock.patch.object(icd_codes, 'BILLABLE_FILE', '/nonexistent/billable.txt'):
            icd_codes.clear_caches()
            with self.assertRaisesMessage(CommandError, 'cannot be checked'):
                self.run_loader(apply=True)
        icd_codes.clear_caches()

    def test_a_failed_replace_leaves_the_old_table(self):
        stale = self.stale_row()
        real = __import__('emr.icd_map', fromlist=['table_fingerprint']).table_fingerprint
        calls = []

        def flaky():
            calls.append(1)
            return real() if len(calls) == 1 else (0, 0)

        with mock.patch('emr.management.commands.load_icd10_map.table_fingerprint', side_effect=flaky):
            with self.assertRaisesMessage(CommandError, 'rolled back'):
                self.run_loader(apply=True)
        self.assertEqual(list(SnomedIcd10Map.objects.values_list('id', flat=True)), [stale.id])


class RepairIcd10CodesTests(IcdFixtureMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.load_map_rows()
        self._n = 0
        self.header = self.problem(CHOL, 'E78.0')            # R1
        self.decided = self.problem(FIT, 'Z00.0')            # R1, through the decision
        self.retired = self.problem(RETIRED, 'R05')          # R2
        self.placeholder = self.problem(SPRAIN, 'S93.4')     # R3
        self.unknown = self.problem(UNKNOWN, 'M25.56')       # R4
        self.no_concept = self.problem('', 'R05')            # R4
        self.legacy = self.problem(DEPRESSION, 'F32.9')      # R5U
        self.fine = self.problem(HTN, 'I10')                 # OK
        self.chosen = self.problem(CHOL, 'K21.9')            # OK: billable, nobody's old pick
        self.blank = self.problem(CHOL, '')                  # not this command's business

    def problem(self, concept, code):
        self._n += 1
        patient = User.objects.create_user(username=f'icdpt{self._n}')
        UserProfile.objects.create(user=patient, role='patient')
        return Problem.objects.create(patient=patient, problem_name=f'p{self._n}', concept_id=concept, icd10_code=code)

    def repair(self, *rules, **kwargs):
        out = StringIO()
        call_command('repair_icd10_codes', apply=list(rules), stdout=out, **kwargs)
        return out.getvalue()

    def code(self, problem):
        problem.refresh_from_db()
        return problem.icd10_code

    def stamped(self, problem):
        return PatientMutationStamp.objects.filter(patient_id=problem.patient_id).exists()

    # -- classification ---------------------------------------------------

    def test_each_stored_code_falls_under_exactly_one_rule(self):
        self.assertEqual(classify(CHOL, 'E78.0'), ('R1', 'E78.00', None))
        self.assertEqual(classify(FIT, 'Z00.0'), ('R1', 'Z00.00', None))
        self.assertEqual(classify(RETIRED, 'R05'), ('R2', 'R05.9', COUGH))
        self.assertEqual(classify(SPRAIN, 'S93.4'), ('R3', '', None))
        self.assertEqual(classify(SPRAIN, 'S93.409?'), ('R3', '', None))
        self.assertEqual(classify(UNKNOWN, 'M25.56'), ('R4', None, None))
        self.assertEqual(classify('', 'R05'), ('R4', None, None))
        self.assertEqual(classify(DEPRESSION, 'F32.9'), ('R5U', 'F32.A', None))
        self.assertEqual(classify(HTN, 'I10'), ('OK', None, None))
        self.assertEqual(classify(CHOL, 'K21.9'), ('OK', None, None))
        self.assertEqual(classify(DERM, 'L30.9'), ('OK', None, None))
        self.assertEqual(classify(CHOL, ''), (None, None, None))

    def test_a_decision_turns_an_unreviewed_old_pick_into_r5_or_leaves_it(self):
        self.write_decisions({DEPRESSION: 'F32.A'})
        self.assertEqual(classify(DEPRESSION, 'F32.9'), ('R5', 'F32.A', None))
        self.write_decisions({DEPRESSION: 'F32.9'})   # the owner chose to keep it
        self.assertEqual(classify(DEPRESSION, 'F32.9'), ('OK', None, None))

    # -- the command -------------------------------------------------------

    def test_a_dry_run_writes_nothing_and_stamps_nobody(self):
        output = self.repair()
        self.assertIn('Dry run', output)
        self.assertEqual(self.code(self.header), 'E78.0')
        self.assertFalse(PatientMutationStamp.objects.exists())

    def test_the_named_rules_are_written_and_no_others(self):
        self.repair('R1', 'R2', 'R3')

        self.assertEqual(self.code(self.header), 'E78.00')
        self.assertEqual(self.code(self.decided), 'Z00.00')
        self.assertEqual(self.code(self.retired), 'R05.9')
        self.assertEqual(self.retired.concept_id, COUGH)       # the concept advances too
        self.assertEqual(self.code(self.placeholder), '')      # blanked, not given a letter

        self.assertEqual(self.code(self.unknown), 'M25.56')    # R4 is never written
        self.assertEqual(self.code(self.no_concept), 'R05')
        self.assertEqual(self.code(self.legacy), 'F32.9')      # R5U was not named
        self.assertEqual(self.code(self.fine), 'I10')
        self.assertEqual(self.code(self.chosen), 'K21.9')
        self.assertEqual(self.code(self.blank), '')

    def test_only_one_rule_can_be_applied_at_a_time(self):
        self.repair('R3')
        self.assertEqual(self.code(self.placeholder), '')
        self.assertEqual(self.code(self.header), 'E78.0')

    def test_only_the_changed_patients_are_stamped(self):
        self.repair('R1', 'R2', 'R3')
        for problem in (self.header, self.decided, self.retired, self.placeholder):
            self.assertTrue(self.stamped(problem))
        for problem in (self.unknown, self.legacy, self.fine, self.chosen, self.blank):
            self.assertFalse(self.stamped(problem))

    def test_every_change_is_logged_with_its_old_value(self):
        with self.assertLogs('smallbrain.icd_repair', level='INFO') as logs:
            self.repair('R1', 'R2')
        rows = {r['problem_id']: r for r in (json.loads(line.split(':', 2)[2]) for line in logs.output)}
        self.assertEqual(set(rows), {self.header.id, self.decided.id, self.retired.id})
        self.assertEqual(rows[self.header.id]['old_code'], 'E78.0')
        self.assertEqual(rows[self.header.id]['new_code'], 'E78.00')
        self.assertEqual(rows[self.retired.id]['new_concept_id'], COUGH)

    def test_an_unreviewed_old_pick_changes_only_when_asked_for_by_name(self):
        self.repair('R5')
        self.assertEqual(self.code(self.legacy), 'F32.9')
        self.repair('R5U')
        self.assertEqual(self.code(self.legacy), 'F32.A')

    def test_a_reviewed_old_pick_takes_the_decision(self):
        self.write_decisions({DEPRESSION: 'F32.A'})
        self.repair('R5')
        self.assertEqual(self.code(self.legacy), 'F32.A')

    def test_a_second_run_finds_nothing_left(self):
        self.repair('R1', 'R2', 'R3', 'R5U')
        PatientMutationStamp.objects.all().delete()
        output = self.repair('R1', 'R2', 'R3', 'R5U')
        self.assertNotIn('written:', output)
        self.assertFalse(PatientMutationStamp.objects.exists())

    def test_it_refuses_to_run_against_a_table_that_is_not_the_bundled_map(self):
        # Every rule asks the map what the code should be. Against the
        # contaminated table R1 would write WHO codes that happen to be billable.
        SnomedIcd10Map.objects.create(
            snomed_concept_id=COUGH, map_group=1, map_priority=1, icd10_code='R05', map_advice='ALWAYS R05')
        with self.assertRaisesMessage(CommandError, 'not the bundled ICD-10-CM map'):
            self.repair('R1')
        self.assertEqual(self.code(self.header), 'E78.0')

    def test_the_review_list_names_what_needs_a_human(self):
        output = self.repair(list_review=True)
        self.assertIn(f'REVIEW|R4|{UNKNOWN}|M25.56||1', output)
        self.assertIn(f'REVIEW|R5U|{DEPRESSION}|F32.9|F32.A|1', output)
        self.assertNotIn(f'|{CHOL}|', output)
