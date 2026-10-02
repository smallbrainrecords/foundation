"""Pin every problem's usual vitals: the one-off catch-up for the months the
legacy nightly job wasn't running (it stopped on 2026-03-04). Rules and owner
decisions are in `emr.usual_vitals`; from now on the endpoints apply them as
problems are created and re-coded.

    python manage.py apply_usual_vital_pins            # dry run: report only
    python manage.py apply_usual_vital_pins --apply    # write

Before applying it turns history into opt-outs. An "Unpinned <vital>" activity
row on a problem that no longer carries that vital means someone took it off
on purpose, and the catch-up must not put it back. Only the mobile unpin
endpoint writes those rows; the retired web UI wrote none, but the legacy job
re-added any web unpin the next night anyway, so no web removal outlived it.

Safe to re-run: every step is idempotent. Output lines start with `RPT|` so
they can be filtered out of the job's log.
"""
from collections import Counter, defaultdict

from django.core.management.base import BaseCommand

from emr.models import (
    Observation, ObservationPinOptOut, ObservationPinToProblem, Problem, ProblemActivity,
)
from emr.usual_vitals import _Cache, apply_usual_vitals, qualifying_codes_by_concept

UNPIN_PREFIX = 'Unpinned '


class Command(BaseCommand):
    help = "Pin every problem's usual vitals (a dry run unless --apply)."

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Write the changes (default: report only).')

    def _say(self, *fields):
        self.stdout.write('RPT|' + '\t'.join('' if f is None else str(f) for f in fields))

    def handle(self, *args, **options):
        apply = options['apply']
        self._say('mode', 'apply' if apply else 'dry-run')

        rules = qualifying_codes_by_concept()
        self._say('qualifying_pairings', sum(len(codes) for codes in rules.values()), 'concepts', len(rules))
        for concept, codes in sorted(rules.items()):
            name = Problem.objects.filter(concept_id=concept).values_list('problem_name', flat=True).first()
            self._say('rule', concept, name, ','.join(codes))

        history = self.opt_outs_from_history()
        self._say('opt_outs_from_history', sum(len(codes) for codes in history.values()), 'problems', len(history))
        if apply:
            for problem_id, codes in history.items():
                for code in codes:
                    ObservationPinOptOut.objects.get_or_create(problem_id=problem_id, code=code)

        cache = _Cache()
        pinned, created, coded, opted_out, untracked = Counter(), Counter(), Counter(), Counter(), Counter()
        problems_changed, charts_changed = 0, set()
        for problem in Problem.objects.filter(concept_id__in=list(rules)).order_by('id').iterator():
            concept = (problem.concept_id or '').strip()
            outcome = apply_usual_vitals(
                problem,
                codes=rules.get(concept, []),
                dry_run=not apply,
                cache=cache,
                also_opted_out=() if apply else history.get(problem.id, ()),
            )
            for name in outcome.pinned:
                pinned[(concept, name)] += 1
            created.update(outcome.created)
            coded.update(outcome.coded)
            opted_out.update(outcome.opted_out)
            untracked.update(outcome.untracked)
            if outcome.pinned:
                problems_changed += 1
                charts_changed.add(problem.patient_id)

        for (concept, name), n in sorted(pinned.items(), key=lambda item: -item[1]):
            self._say('pinned', concept, name, n)
        for name, n in created.most_common():
            self._say('records_created', name, n)
        for name, n in coded.most_common():
            self._say('uncoded_records_given_code', name, n)
        for code, n in opted_out.most_common():
            self._say('skipped_opted_out', code, n)
        for code, n in untracked.most_common():
            self._say('skipped_no_record', code, n)
        self._say('total_pins', sum(pinned.values()), 'problems', problems_changed, 'charts', len(charts_changed))
        self._say('done')

    @staticmethod
    def opt_outs_from_history():
        """{problem_id: {loinc}} — vitals someone unpinned from a problem that
        does not carry them today."""
        result = defaultdict(set)
        rows = (
            ProblemActivity.objects
            .filter(activity__startswith=UNPIN_PREFIX, problem__isnull=False)
            .values_list('problem_id', 'problem__patient_id', 'activity')
        )
        for problem_id, patient_id, activity in rows:
            name = activity[len(UNPIN_PREFIX):].strip()
            if not name:
                continue
            codes = (
                Observation.objects.filter(subject_id=patient_id, name__iexact=name)
                .exclude(code__isnull=True).exclude(code='')
                .values_list('code', flat=True)
            )
            for code in {c.strip() for c in codes if c and c.strip()}:
                if ObservationPinToProblem.objects.filter(problem_id=problem_id, observation__code=code).exists():
                    continue  # pinned again since; the removal no longer stands
                result[problem_id].add(code)
        return result
