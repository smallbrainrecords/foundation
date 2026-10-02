"""Usual vitals — the rule that pins a problem's habitual vitals for it.

Owner decisions 2026-10-01 live in `emr.usual_vitals`'s docstring; several of
these assertions encode them (INR is never automatic, a pin someone removed
stays removed, automatic pins never authenticate a problem, records are only
created for vitals most charts with the problem already track).
"""
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase

from emr.models import (
    Observation, ObservationComponent, ObservationPinOptOut, ObservationPinToProblem,
    ObservationUnit, Problem, ProblemActivity, UserProfile,
)
from emr.usual_vitals import (
    _Cache, apply_usual_vitals, propagate_if_newly_qualified, qualifying_codes,
    qualifying_codes_by_concept,
)

DM2 = '44054006'
HTN = '38341003'
AFIB = '49436004'
A1C = '4548-4'
WEIGHT = '3141-9'
BP = '85354-9'
INR = '6301-6'


class UsualVitalsTestBase(TestCase):
    def setUp(self):
        self.physician = self.user('doc', 'physician')
        self.nurse = self.user('nurse', 'nurse')
        self._patients = 0

    def user(self, name, role):
        user = User.objects.create_user(username=name)
        UserProfile.objects.create(user=user, role=role)
        return user

    def patient(self):
        self._patients += 1
        return self.user(f'pt{self._patients}', 'patient')

    def problem(self, patient, concept, name='Problem', active=True):
        return Problem.objects.create(
            patient=patient, problem_name=name, concept_id=concept, is_active=active)

    def record(self, patient, code, name, components=None, unit=None):
        observation = Observation.objects.create(subject=patient, name=name, code=code)
        for comp_name, comp_code in components or [(name, code)]:
            ObservationComponent.objects.create(
                observation=observation, name=comp_name, component_code=comp_code)
        if unit:
            ObservationUnit.objects.create(observation=observation, value_unit=unit, is_used=True)
        return observation

    def pin(self, observation, problem, author=None):
        return ObservationPinToProblem.objects.create(
            observation=observation, problem=problem, author=author)

    def seed_pairing(self, concept, code, name, charts=3, author='physician', **record_kwargs):
        """`charts` patients each with the problem, a record, and a pin."""
        author_user = {'physician': self.physician, 'nurse': self.nurse, None: None}[author]
        for _ in range(charts):
            patient = self.patient()
            problem = self.problem(patient, concept)
            self.pin(self.record(patient, code, name, **record_kwargs), problem, author_user)

    def pinned_codes(self, problem):
        return set(
            ObservationPinToProblem.objects.filter(problem=problem)
            .values_list('observation__code', flat=True))


class QualifyingRuleTests(UsualVitalsTestBase):

    def test_qualifies_at_three_charts_pinned_by_a_physician(self):
        self.seed_pairing(DM2, A1C, 'a1c', charts=2)
        self.assertEqual(qualifying_codes(DM2), [])
        self.seed_pairing(DM2, A1C, 'a1c', charts=1)
        self.assertEqual(qualifying_codes(DM2), [A1C])

    def test_counted_per_chart_not_per_pin(self):
        patient = self.patient()
        record = self.record(patient, A1C, 'a1c')
        for _ in range(3):
            self.pin(record, self.problem(patient, DM2), self.physician)
        self.assertEqual(qualifying_codes(DM2), [])

    def test_pins_by_others_and_by_the_rule_itself_do_not_count(self):
        self.seed_pairing(DM2, A1C, 'a1c', charts=3, author='nurse')
        self.seed_pairing(DM2, A1C, 'a1c', charts=3, author=None)
        self.assertEqual(qualifying_codes(DM2), [])

    def test_a_blank_concept_is_not_a_concept(self):
        # The legacy job's bug: three pins on free-text problems taught it to
        # pin weight to EVERY free-text problem.
        self.seed_pairing('', WEIGHT, 'weight', charts=3)
        self.assertNotIn('', qualifying_codes_by_concept())
        free_text = self.problem(self.patient(), '')
        self.assertEqual(apply_usual_vitals(free_text).pinned, [])

    def test_inr_never_qualifies(self):
        # Owner, 2026-10-01: "don't include the INR automatically".
        self.seed_pairing(AFIB, INR, 'INR', charts=5)
        self.assertEqual(qualifying_codes(AFIB), [])

    def test_retired_phq2_never_qualifies(self):
        self.seed_pairing('102499006', '55757-9', 'PHQ-2', charts=5)
        self.assertEqual(qualifying_codes('102499006'), [])


class ApplyTests(UsualVitalsTestBase):

    def setUp(self):
        super().setUp()
        self.seed_pairing(HTN, WEIGHT, 'weight', charts=3, unit='lb')

    def test_pins_the_charts_existing_record_without_an_author(self):
        patient = self.patient()
        weight = self.record(patient, WEIGHT, 'weight')
        problem = self.problem(patient, HTN, 'Hypertension')

        outcome = apply_usual_vitals(problem)

        self.assertEqual(outcome.pinned, ['weight'])
        pin = ObservationPinToProblem.objects.get(problem=problem)
        self.assertEqual(pin.observation, weight)
        self.assertIsNone(pin.author)
        self.assertTrue(ProblemActivity.objects.filter(
            problem=problem, author=None, activity__startswith='Automatically pinned weight').exists())

    def test_running_twice_pins_nothing_more(self):
        patient = self.patient()
        self.record(patient, WEIGHT, 'weight')
        problem = self.problem(patient, HTN)
        apply_usual_vitals(problem)
        activity_rows = ProblemActivity.objects.filter(problem=problem).count()

        self.assertEqual(apply_usual_vitals(problem).pinned, [])
        self.assertEqual(ObservationPinToProblem.objects.filter(problem=problem).count(), 1)
        self.assertEqual(ProblemActivity.objects.filter(problem=problem).count(), activity_rows)

    def test_a_vital_pinned_through_a_duplicate_record_counts_as_pinned(self):
        patient = self.patient()
        self.record(patient, WEIGHT, 'weight')
        second = self.record(patient, WEIGHT, 'weight')
        problem = self.problem(patient, HTN)
        self.pin(second, problem, self.nurse)

        self.assertEqual(apply_usual_vitals(problem).pinned, [])
        self.assertEqual(ObservationPinToProblem.objects.filter(problem=problem).count(), 1)

    def test_a_vital_someone_unpinned_stays_unpinned(self):
        patient = self.patient()
        self.record(patient, WEIGHT, 'weight')
        problem = self.problem(patient, HTN)
        ObservationPinOptOut.objects.create(problem=problem, code=WEIGHT)

        outcome = apply_usual_vitals(problem)

        self.assertEqual(outcome.pinned, [])
        self.assertEqual(outcome.opted_out, [WEIGHT])
        self.assertFalse(ObservationPinToProblem.objects.filter(problem=problem).exists())

    def test_never_touches_the_authenticated_flag(self):
        patient = self.patient()
        self.record(patient, WEIGHT, 'weight')
        for flag in (False, True):
            problem = self.problem(patient, HTN)
            Problem.objects.filter(pk=problem.pk).update(authenticated=flag)
            problem.refresh_from_db()
            apply_usual_vitals(problem)
            problem.refresh_from_db()
            self.assertEqual(problem.authenticated, flag)

    def test_dry_run_writes_nothing(self):
        patient = self.patient()
        self.record(patient, WEIGHT, 'weight')
        problem = self.problem(patient, HTN)

        outcome = apply_usual_vitals(problem, dry_run=True)

        self.assertEqual(outcome.pinned, ['weight'])
        self.assertFalse(ObservationPinToProblem.objects.filter(problem=problem).exists())
        self.assertFalse(ProblemActivity.objects.filter(problem=problem).exists())


class MissingRecordTests(UsualVitalsTestBase):

    def test_created_when_most_charts_with_the_problem_track_the_vital(self):
        self.seed_pairing(DM2, A1C, 'a1c', charts=3, unit='%')
        patient = self.patient()
        problem = self.problem(patient, DM2, 'Diabetes mellitus type 2')

        outcome = apply_usual_vitals(problem)

        self.assertEqual(outcome.created, ['a1c'])
        record = Observation.objects.get(subject=patient, code=A1C)
        self.assertEqual(record.name, 'a1c')
        self.assertEqual(
            list(record.observation_components.values_list('component_code', flat=True)), [A1C])
        self.assertEqual(record.observation_units.get(is_used=True).value_unit, '%')
        self.assertTrue(ObservationPinToProblem.objects.filter(problem=problem, observation=record).exists())

    def test_skipped_when_most_charts_with_the_problem_do_not_track_it(self):
        self.seed_pairing(DM2, A1C, 'a1c', charts=3)
        # Four more diabetics with no A1C record: 3 of 8 charts track it.
        for _ in range(4):
            self.problem(self.patient(), DM2)
        patient = self.patient()
        problem = self.problem(patient, DM2)

        outcome = apply_usual_vitals(problem)

        self.assertEqual(outcome.untracked, [A1C])
        self.assertFalse(Observation.objects.filter(subject=patient).exists())

    def test_never_created_for_an_inactive_problem(self):
        self.seed_pairing(DM2, A1C, 'a1c', charts=3)
        patient = self.patient()
        problem = self.problem(patient, DM2, active=False)

        self.assertEqual(apply_usual_vitals(problem).untracked, [A1C])
        self.assertFalse(Observation.objects.filter(subject=patient).exists())

    def test_a_blood_pressure_record_gets_each_side_once(self):
        pair = [('Systolic', '8480-6'), ('Diastolic', '8462-4')]
        self.seed_pairing(HTN, BP, 'blood pressure', charts=3, components=pair + pair, unit='mmHg')
        patient = self.patient()

        apply_usual_vitals(self.problem(patient, HTN))

        record = Observation.objects.get(subject=patient, code=BP)
        self.assertEqual(
            list(record.observation_components.order_by('id').values_list('name', 'component_code')), pair)

    def test_uses_the_name_most_charts_use(self):
        self.seed_pairing(DM2, '2345-7', 'Glucose', charts=3, unit='mg/dL')
        patient = self.patient()
        self.record(patient, '2345-7', 'blood glucose')  # an odd one out elsewhere
        self.problem(patient, DM2)
        newcomer = self.patient()

        apply_usual_vitals(self.problem(newcomer, DM2))

        self.assertEqual(Observation.objects.get(subject=newcomer, code='2345-7').name, 'Glucose')


    def test_a_record_with_no_code_is_the_charts_record(self):
        # Prod 2026-10-01: one chart tracked glucose in a record that never got
        # a LOINC code, and the backfill would have minted a second "Glucose".
        self.seed_pairing(DM2, '2345-7', 'Glucose', charts=3, unit='mg/dL')
        patient = self.patient()
        legacy = Observation.objects.create(subject=patient, name='glucose', code='')
        problem = self.problem(patient, DM2)

        outcome = apply_usual_vitals(problem)

        self.assertEqual(outcome.created, [])
        self.assertEqual(outcome.coded, ['glucose'])
        self.assertEqual(Observation.objects.filter(subject=patient).count(), 1)
        legacy.refresh_from_db()
        self.assertEqual(legacy.code, '2345-7')
        self.assertTrue(ObservationPinToProblem.objects.filter(problem=problem, observation=legacy).exists())

    def test_an_uncoded_record_already_pinned_is_left_alone(self):
        self.seed_pairing(DM2, '2345-7', 'Glucose', charts=3)
        patient = self.patient()
        legacy = Observation.objects.create(subject=patient, name='Glucose', code=None)
        problem = self.problem(patient, DM2)
        self.pin(legacy, problem, self.nurse)

        self.assertEqual(apply_usual_vitals(problem).pinned, [])
        self.assertEqual(ObservationPinToProblem.objects.filter(problem=problem).count(), 1)
        self.assertEqual(Observation.objects.filter(subject=patient).count(), 1)

    def test_an_uncoded_record_of_another_vital_is_not_taken(self):
        self.seed_pairing(DM2, '2345-7', 'Glucose', charts=3)
        patient = self.patient()
        Observation.objects.create(subject=patient, name='Weight', code='')
        problem = self.problem(patient, DM2)

        outcome = apply_usual_vitals(problem)

        self.assertEqual(outcome.coded, [])
        self.assertEqual(outcome.created, ['Glucose'])

    def test_a_dry_run_counts_a_new_record_once_per_chart(self):
        # Prod's first dry run reported 150 new records where 118 would be
        # made: a chart with two qualifying problems was counted per problem.
        self.seed_pairing(DM2, A1C, 'a1c', charts=3)
        patient = self.patient()
        first, second = self.problem(patient, DM2), self.problem(patient, DM2)

        cache = _Cache()
        outcomes = [apply_usual_vitals(p, dry_run=True, cache=cache) for p in (first, second)]
        self.assertEqual([o.created for o in outcomes], [['a1c'], []])
        self.assertEqual([o.pinned for o in outcomes], [['a1c'], ['a1c']])

        # The real run agrees: one record, two pins.
        for p in (first, second):
            apply_usual_vitals(p, cache=_Cache())
        self.assertEqual(Observation.objects.filter(subject=patient, code=A1C).count(), 1)
        self.assertEqual(ObservationPinToProblem.objects.filter(problem__in=[first, second]).count(), 2)


class PropagationTests(UsualVitalsTestBase):

    def test_the_pin_that_makes_a_pairing_qualify_reaches_every_chart(self):
        self.seed_pairing(HTN, WEIGHT, 'weight', charts=2)
        others = []
        for _ in range(3):
            patient = self.patient()
            self.record(patient, WEIGHT, 'weight')
            others.append(self.problem(patient, HTN))
        third = self.patient()
        pin = self.pin(self.record(third, WEIGHT, 'weight'), self.problem(third, HTN), self.physician)

        self.assertEqual(propagate_if_newly_qualified(pin), 3)
        for problem in others:
            self.assertEqual(self.pinned_codes(problem), {WEIGHT})

    def test_fires_only_at_the_crossing(self):
        self.seed_pairing(HTN, WEIGHT, 'weight', charts=1)
        patient = self.patient()
        self.record(patient, WEIGHT, 'weight')
        bystander = self.problem(patient, HTN)

        def physician_pin_on_a_new_chart():
            chart = self.patient()
            return self.pin(self.record(chart, WEIGHT, 'weight'), self.problem(chart, HTN), self.physician)

        self.assertEqual(propagate_if_newly_qualified(physician_pin_on_a_new_chart()), 0)  # 2 charts
        self.assertEqual(self.pinned_codes(bystander), set())
        self.assertEqual(propagate_if_newly_qualified(physician_pin_on_a_new_chart()), 1)  # 3: crossing
        ObservationPinToProblem.objects.filter(problem=bystander).delete()
        # Past the crossing it's the creation hook's job, not this one.
        self.assertEqual(propagate_if_newly_qualified(physician_pin_on_a_new_chart()), 0)  # 4 charts
        self.assertEqual(self.pinned_codes(bystander), set())

    def test_inr_does_not_propagate(self):
        self.seed_pairing(AFIB, INR, 'INR', charts=2)
        patient = self.patient()
        self.record(patient, INR, 'INR')
        bystander = self.problem(patient, AFIB)
        third = self.patient()
        pin = self.pin(self.record(third, INR, 'INR'), self.problem(third, AFIB), self.physician)

        self.assertEqual(propagate_if_newly_qualified(pin), 0)
        self.assertEqual(self.pinned_codes(bystander), set())


class BackfillCommandTests(UsualVitalsTestBase):

    def setUp(self):
        super().setUp()
        self.seed_pairing(HTN, WEIGHT, 'weight', charts=3)
        self.patient_a = self.patient()
        self.record(self.patient_a, WEIGHT, 'weight')
        self.problem_a = self.problem(self.patient_a, HTN)

    def run_command(self, *args):
        out = StringIO()
        call_command('apply_usual_vital_pins', *args, stdout=out)
        return out.getvalue()

    def test_dry_run_reports_and_writes_nothing(self):
        report = self.run_command()
        self.assertIn('RPT|total_pins\t1\t', report)
        self.assertFalse(ObservationPinToProblem.objects.filter(problem=self.problem_a).exists())

    def test_apply_pins(self):
        report = self.run_command('--apply')
        self.assertIn('RPT|total_pins\t1\t', report)
        self.assertEqual(self.pinned_codes(self.problem_a), {WEIGHT})

    def test_a_vital_unpinned_in_the_past_is_not_put_back(self):
        ProblemActivity.objects.create(problem=self.problem_a, author=self.physician, activity='Unpinned weight')

        dry = self.run_command()
        self.assertIn('RPT|total_pins\t0\t', dry)
        self.run_command('--apply')

        self.assertEqual(self.pinned_codes(self.problem_a), set())
        self.assertTrue(ObservationPinOptOut.objects.filter(problem=self.problem_a, code=WEIGHT).exists())

    def test_an_unpin_since_reversed_by_hand_is_not_an_opt_out(self):
        weight = Observation.objects.get(subject=self.patient_a, code=WEIGHT)
        ProblemActivity.objects.create(problem=self.problem_a, author=self.physician, activity='Unpinned weight')
        self.pin(weight, self.problem_a, self.nurse)

        self.run_command('--apply')

        self.assertFalse(ObservationPinOptOut.objects.filter(problem=self.problem_a).exists())

    def test_an_uncoded_record_is_reported_and_coded_not_duplicated(self):
        other = self.patient()
        legacy = Observation.objects.create(subject=other, name='weight', code='')
        self.problem(other, HTN)

        dry = self.run_command()
        self.assertIn('RPT|uncoded_records_given_code\tweight\t1', dry)
        self.assertNotIn('RPT|records_created', dry)
        legacy.refresh_from_db()
        self.assertEqual(legacy.code, '', 'a dry run writes nothing')

        self.run_command('--apply')
        legacy.refresh_from_db()
        self.assertEqual(legacy.code, WEIGHT)
        self.assertEqual(Observation.objects.filter(subject=other).count(), 1)
