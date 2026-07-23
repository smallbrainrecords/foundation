"""Backfill + repair ICD-10 codes on Problems from the SNOMED map.

Two independent passes, each with its own flag (default is dry-run for both):

**Backfill** — Django auto-assigns an ICD-10 from `SnomedIcd10Map` when a
problem is created or edited without one (`mobile_api/views.py`), but problems
created before that logic — or never edited since — carry a SNOMED concept and
no ICD. This is a generalization of `map_top_500` (which only touched the
top-500 concepts): it backfills EVERY problem whose concept has a mapping.
Only empty/NULL `icd10_code` rows are touched.

**Conditional-pick repair** — before 2026-07-23 the auto-assign (and
`map_top_500`) picked `.first()` under `(map_group, map_priority)` ordering,
which can select a CONDITIONAL map-rule gate ("IF AGE ... BEFORE 29.0 DAYS")
over the unconditional `ALWAYS` default — e.g. hypertension stored the neonatal
P29.2 instead of I10. `--fix-conditional` corrects ONLY rows provably written
by that bug: stored code == the old buggy pick, where old pick != corrected
pick. Stored codes matching NEITHER pick (staged CommonProblem codes, legacy
web-era data, older map releases) are deliberately never touched — they may be
deliberate clinical choices.

Both passes pick via `SnomedIcd10Map.best_icd10_for` (unconditional-first),
the same helper the live auto-assign now uses.

Concepts with NO mapping row are left untouched and reported as a count only
(the review/curation of unmapped concepts is deliberately out of scope).

Usage:
    python manage.py backfill_icd10                          # dry run both passes
    python manage.py backfill_icd10 --apply                  # write backfill
    python manage.py backfill_icd10 --fix-conditional        # write repairs
    python manage.py backfill_icd10 --apply --fix-conditional  # write both

Safe to dry-run against prod. Writes are per-concept bulk UPDATEs.
"""
from django.core.management.base import BaseCommand
from django.db.models import Q

from emr.models import Problem, SnomedIcd10Map


def _old_buggy_pick(concept_id):
    """The pre-2026-07-23 pick: plain .first() under (group, priority, id)."""
    row = (
        SnomedIcd10Map.objects
        .filter(snomed_concept_id=concept_id)
        .order_by("map_group", "map_priority", "id")
        .first()
    )
    return row.icd10_code if row else None


class Command(BaseCommand):
    help = "Backfill missing ICD-10 codes and repair buggy conditional picks on Problems."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Write the backfill (missing codes). Without it, report only.",
        )
        parser.add_argument(
            "--fix-conditional",
            action="store_true",
            help=(
                "Write the conditional-pick repair (stored code == old buggy "
                "pick != corrected pick). Without it, report only."
            ),
        )

    def handle(self, *args, **options):
        self.backfill_pass(apply=options["apply"])
        self.stdout.write("")
        self.repair_pass(apply=options["fix_conditional"])

    # ------------------------------------------------------------- backfill

    def backfill_pass(self, apply):
        needs_backfill = Problem.objects.filter(
            Q(icd10_code__isnull=True) | Q(icd10_code=""),
        ).exclude(
            Q(concept_id__isnull=True) | Q(concept_id=""),
        )

        total_candidates = needs_backfill.count()
        concept_ids = list(
            needs_backfill.values_list("concept_id", flat=True).distinct()
        )

        self.stdout.write("=== ICD-10 backfill (missing codes) ===")
        self.stdout.write(f"mode                       : {'APPLY' if apply else 'dry-run'}")
        self.stdout.write(f"problems missing icd10     : {total_candidates}")
        self.stdout.write(f"distinct concepts involved : {len(concept_ids)}")

        mapped_rows = 0
        mapped_concepts = 0
        unmapped_rows = 0
        unmapped_concepts = 0

        for concept_id in concept_ids:
            best = SnomedIcd10Map.best_icd10_for(concept_id)

            concept_qs = needs_backfill.filter(concept_id=concept_id)

            if best is None:
                unmapped_concepts += 1
                unmapped_rows += concept_qs.count()
                continue

            mapped_concepts += 1
            if apply:
                updated = concept_qs.update(icd10_code=best)
            else:
                updated = concept_qs.count()
            mapped_rows += updated

        self.stdout.write(f"mapped concepts            : {mapped_concepts}")
        self.stdout.write(
            f"rows {'updated' if apply else 'that would update'}   : {mapped_rows}"
        )
        self.stdout.write(f"unmapped concepts (skipped): {unmapped_concepts}")
        self.stdout.write(f"unmapped rows (skipped)    : {unmapped_rows}")

        if not apply:
            self.stdout.write("Dry run — nothing written. Use --apply to write.")

    # --------------------------------------------------------------- repair

    def repair_pass(self, apply):
        has_code = Problem.objects.exclude(
            Q(icd10_code__isnull=True) | Q(icd10_code=""),
        ).exclude(
            Q(concept_id__isnull=True) | Q(concept_id=""),
        )

        concept_ids = list(
            has_code.values_list("concept_id", flat=True).distinct()
        )

        self.stdout.write("=== Conditional-pick repair (stored == old buggy pick) ===")
        self.stdout.write(f"mode                       : {'APPLY' if apply else 'dry-run'}")
        self.stdout.write(f"problems with stored icd10 : {has_code.count()}")
        self.stdout.write(f"distinct concepts involved : {len(concept_ids)}")

        repaired_rows = 0
        repaired_concepts = 0
        untouched_other_code = 0

        for concept_id in concept_ids:
            new_pick = SnomedIcd10Map.best_icd10_for(concept_id)
            if new_pick is None:
                continue
            old_pick = _old_buggy_pick(concept_id)
            concept_qs = has_code.filter(concept_id=concept_id)

            if old_pick == new_pick:
                # Pick never changed for this concept; stored codes that differ
                # are from other sources and stay untouched.
                untouched_other_code += concept_qs.exclude(icd10_code=new_pick).count()
                continue

            buggy_qs = concept_qs.filter(icd10_code=old_pick)
            untouched_other_code += (
                concept_qs.exclude(icd10_code=old_pick)
                .exclude(icd10_code=new_pick)
                .count()
            )

            if apply:
                updated = buggy_qs.update(icd10_code=new_pick)
            else:
                updated = buggy_qs.count()
            if updated:
                repaired_concepts += 1
                repaired_rows += updated

        self.stdout.write(f"concepts with buggy rows   : {repaired_concepts}")
        self.stdout.write(
            f"rows {'repaired' if apply else 'that would repair'}  : {repaired_rows}"
        )
        self.stdout.write(
            f"other-source codes (kept)  : {untouched_other_code}"
        )

        if not apply:
            self.stdout.write("Dry run — nothing written. Use --fix-conditional to write.")
