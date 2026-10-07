"""Repair Problems whose stored ICD-10 code is not a billable ICD-10-CM code.

    python manage.py repair_icd10_codes                     # dry run: full report
    python manage.py repair_icd10_codes --apply R1 R2 R3    # write the named rules
    python manage.py repair_icd10_codes --list-review       # also print what needs a human

Background (2026-10-06): the SNOMED -> ICD-10 map table had been loaded from
the wrong file (see `load_icd10_map`), and for months both the server's
auto-assign and the app's bundled map stamped codes from it. In production
7,830 of 24,272 coded problems carried a code a lab cannot bill: 6,196 category
headers (`E78.0`, `M54.5`, `R05`), 1,276 WHO ICD-10 codes that are not
ICD-10-CM at all (`R07.4`), and 358 `?` placeholders.

Run this AFTER `load_icd10_map --apply`: every rule asks the map what the code
should be, so it refuses to run while the table is not the bundled one.

The rules. Each row is classified by exactly one, on its (concept, stored
code); nothing is written for a rule that was not named in `--apply`.

  R1   stored code is not billable; the concept has an assignable code
       (the owner's decision, else the map's pick)        -> set the code
  R2   stored code is not billable; the concept is retired with a safe
       successor that has one             -> advance the concept, set the code
  R3   stored code is not billable; the map's answer is a `?` placeholder
       (injuries, poisonings: the 7th character depends on the visit)
                                                          -> blank the code
  R4   stored code is not billable; nothing can be assigned
                                    -> never written; listed for review
  R5   stored code is billable but is the OLD table's pick, and the owner
       has since recorded a different decision for the concept
                                                          -> set the decision
  R5U  as R5 but with no decision recorded: the clean map simply assigns a
       different billable code (depression F32.9 -> F32.A). Review these
       concepts first; applying R5U is the "take the map's word for all of
       them" switch and is never implied by the others.

Never touched, whatever is applied: a billable code that is not the old
table's pick. That is either already right, one of the owner's recorded
decisions, or a choice somebody made.

Like the other data heals this writes no ProblemActivity row and does not
change `authenticated`. It does touch each affected patient's
PatientMutationStamp, so the Macs pull the new codes, and it logs one
`smallbrain.icd_repair` row per problem with the old and new values — that log
is the undo record.

Idempotent: a repaired row no longer matches any rule. Re-run it after each
review round and after each terminology release.
"""
import json
import logging
from collections import Counter, defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Count, Q

from emr.icd_codes import (
    billable_codes, decision_for, explain_assignable, is_billable, legacy_pick_for,
    normalize, placeholder_pick_for,
)
from emr.icd_map import MapFileError, table_matches_bundled_map
from emr.models import Problem
from emr.mutation_stamp import touch_patient_stamp

_LOGGER = logging.getLogger('smallbrain.icd_repair')

WRITE_RULES = ('R1', 'R2', 'R3', 'R5', 'R5U')
DESCRIPTIONS = {
    'R1': 'not billable -> the concept\'s assignable code',
    'R2': 'not billable -> retired concept advanced to its successor',
    'R3': 'not billable, map gives a ? placeholder -> blank',
    'R4': 'not billable, nothing assignable (review; never written)',
    'R5': 'old table\'s pick, owner decided otherwise -> the decision',
    'R5U': 'old table\'s pick, map assigns another code (unreviewed)',
    'OK': 'billable and left alone',
}


def classify(concept_id, stored_code):
    """(rule, new_code, new_concept) for one stored (concept, code) pair.

    Pure apart from the map lookups, so the rules can be tested without the
    command. `new_concept` is set only for R2.
    """
    concept = (concept_id or '').strip()
    stored = normalize(stored_code)
    if not stored:
        return None, None, None

    if is_billable(stored):
        if concept and legacy_pick_for(concept) == stored:
            decided = decision_for(concept)
            if decided:
                return ('R5', decided, None) if decided != stored else ('OK', None, None)
            target = explain_assignable(concept)[0]
            if target and target != stored:
                return 'R5U', target, None
        return 'OK', None, None

    if not concept:
        return 'R4', None, None
    target, source, target_concept = explain_assignable(concept)
    if target:
        if source == 'successor':
            return 'R2', target, target_concept
        return 'R1', target, None
    if placeholder_pick_for(concept):
        return 'R3', '', None
    return 'R4', None, None


class Command(BaseCommand):
    help = 'Repair Problems whose ICD-10 code is not billable ICD-10-CM (dry run unless --apply RULE ...).'

    def add_arguments(self, parser):
        parser.add_argument('--apply', nargs='+', default=[], metavar='RULE', choices=WRITE_RULES,
                            help='Rules to write: any of R1 R2 R3 R5 R5U. Omit for a dry run.')
        parser.add_argument('--list-review', action='store_true',
                            help='Print every R4 and R5U group as a REVIEW| line.')
        parser.add_argument('--allow-unverified-map', action='store_true',
                            help='Run even if the map table is not the bundled map (tests only).')

    def handle(self, *args, **options):
        apply_rules = set(options['apply'])

        if billable_codes() is None:
            raise CommandError('The billable-code list is missing; nothing can be classified.')
        if not options['allow_unverified_map']:
            try:
                current = table_matches_bundled_map()
            except MapFileError as exc:
                raise CommandError(str(exc))
            if not current:
                raise CommandError(
                    'The map table is not the bundled ICD-10-CM map. Run '
                    '`load_icd10_map --apply` first — every rule here asks the map '
                    'what the code should be.'
                )

        groups = (
            Problem.objects
            .exclude(Q(icd10_code__isnull=True) | Q(icd10_code=''))
            .values('concept_id', 'icd10_code')
            .annotate(n=Count('id'))
            .order_by()
        )

        problems, concepts = Counter(), defaultdict(set)
        examples, work, review = defaultdict(Counter), [], []
        for group in groups:
            concept, code, n = group['concept_id'], group['icd10_code'], group['n']
            rule, new_code, new_concept = classify(concept, code)
            if rule is None:
                continue
            problems[rule] += n
            concepts[rule].add((concept or '').strip())
            examples[rule][(concept or '-', code, new_code if new_code else '-')] += n
            if rule in WRITE_RULES:
                work.append((rule, concept, code, new_code, new_concept, n))
            if rule in ('R4', 'R5U'):
                review.append((rule, concept or '', code, new_code or '', n))

        self.stdout.write('=== Repair ICD-10 codes ===')
        self.stdout.write(f"mode  : {'APPLY ' + ' '.join(sorted(apply_rules)) if apply_rules else 'dry-run'}")
        for rule in ('R1', 'R2', 'R3', 'R4', 'R5', 'R5U', 'OK'):
            if not problems[rule]:
                continue
            self.stdout.write(
                f"{rule:<4} {problems[rule]:>6} problems  {len(concepts[rule]):>5} concepts   {DESCRIPTIONS[rule]}"
            )
            if rule != 'OK':
                for (concept, old, new), n in examples[rule].most_common(4):
                    self.stdout.write(f"       {n:>5}  {concept:<18} {old:<10} -> {new}")

        if options['list_review']:
            self.stdout.write('')
            self.stdout.write('REVIEW|rule|concept|stored|map_suggests|problems')
            for rule, concept, code, suggested, n in sorted(review, key=lambda r: (r[0], -r[4])):
                self.stdout.write(f'REVIEW|{rule}|{concept}|{code}|{suggested}|{n}')

        if not apply_rules:
            self.stdout.write('')
            self.stdout.write('Dry run — nothing written. Name the rules to write: --apply R1 R2 R3')
            return

        written, patients = Counter(), set()
        for rule, concept, code, new_code, new_concept, _ in work:
            if rule not in apply_rules:
                continue
            rows = Problem.objects.filter(icd10_code=code)
            rows = rows.filter(concept_id__isnull=True) if concept is None else rows.filter(concept_id=concept)
            with transaction.atomic():
                affected = list(rows.values_list('id', 'patient_id'))
                if not affected:
                    continue
                fields = {'icd10_code': new_code}
                if new_concept:
                    fields['concept_id'] = new_concept
                Problem.objects.filter(id__in=[pk for pk, _ in affected]).update(**fields)
            for problem_id, patient_id in affected:
                _LOGGER.info(json.dumps({
                    'event': 'icd_repaired',
                    'rule': rule,
                    'problem_id': problem_id,
                    'patient_id': patient_id,
                    'concept_id': concept or '',
                    'old_code': code,
                    'new_code': new_code,
                    **({'new_concept_id': new_concept} if new_concept else {}),
                }))
                if patient_id:
                    patients.add(patient_id)
            written[rule] += len(affected)

        # A bulk UPDATE writes no mutation stamp; without this the corrected
        # codes sit on the server until someone manually refreshes a chart.
        stamped = 0
        for patient_id in patients:
            try:
                touch_patient_stamp(patient_id)
                stamped += 1
            except Exception:  # best-effort; never fail a completed repair
                pass

        self.stdout.write('')
        for rule in sorted(written):
            self.stdout.write(f'{rule} written: {written[rule]} problems')
        self.stdout.write(f'patients affected      : {len(patients)}')
        self.stdout.write(f'mutation stamps touched: {stamped}')
