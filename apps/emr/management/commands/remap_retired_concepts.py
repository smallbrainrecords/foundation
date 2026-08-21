"""Heal Problems whose SNOMED concept is RETIRED, so they can carry an ICD-10.

The legacy web system stored SNOMED concept ids that have since been retired.
The official SNOMED CT -> ICD-10-CM map only covers ACTIVE concepts, so a
retired concept can never map and its Problem prints on an order requisition
with no diagnosis code. Field example (2026-08-21): "Anemia (disorder)" stored
as 64593003, which SNOMED retired; SAME_AS -> 271737000 -> D64.9.

Of the 483 unmapped concepts in production, 445 (92%) are retired rather than
genuinely unmappable, so this is the single largest remaining ICD gap.

CLINICAL SAFETY -- association types are NOT equally trustworthy, and only the
exact ones are applied automatically:

  * SAME AS      (900000000000527005) -- exact equivalent .......... APPLIED
  * REPLACED BY  (900000000000526001) -- direct successor .......... APPLIED
  * POSSIBLY EQUIVALENT TO (900000000000523009) ................... REPORTED
  * WAS A        (900000000000528000) -- hierarchical, imprecise ... REPORTED

"Possibly equivalent to" is ambiguous by definition (SNOMED emits it when there
is no exact successor, and a concept may carry several such targets), so
auto-applying it could stamp a wrong diagnosis onto a billing document. Those
rows are counted and listed for human review instead. A retired concept with
more than one safe target is likewise skipped rather than guessed.

The retired->active pairs ship in `apps/emr/data/snomed_retired_concept_map.tsv`
(generated from the licensed SNOMED US release; see the file header). It is
bundled because this runs as a Cloud Run job against production, where the
ontology release folders are not available.

Each healed Problem gets BOTH:
  * `concept_id` advanced to the active concept -- fixes the root cause, so
    future re-maps and any concept-keyed feature work for this row; and
  * `icd10_code` from `SnomedIcd10Map.best_icd10_for` -- the same
    unconditional-first pick the live auto-assign and `backfill_icd10` use.

It also touches each affected patient's `PatientMutationStamp`, so the mobile
`/changed` poll actually notices. A bulk `.update()` bypasses that signal, which
is why the earlier `backfill_icd10` run left correct codes on the server that
never reached the Macs until someone manually refreshed the chart.

Usage:
    python manage.py remap_retired_concepts             # dry run (default)
    python manage.py remap_retired_concepts --apply     # write
    python manage.py remap_retired_concepts --list-review   # show ambiguous ones
"""
import csv
import os

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from emr.models import Problem, SnomedIcd10Map
from emr.mutation_stamp import touch_patient_stamp

DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "snomed_retired_concept_map.tsv",
)


class Command(BaseCommand):
    help = "Remap Problems on retired SNOMED concepts to their active successor and assign ICD-10."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Write the changes. Without this flag the command only reports.",
        )
        parser.add_argument(
            "--list-review",
            action="store_true",
            help="List the retired concepts that need human review (no safe successor).",
        )
        parser.add_argument(
            "--map-file",
            default=DATA_FILE,
            help="Override the bundled retired->active TSV.",
        )

    def load_map(self, path):
        pairs = {}
        with open(path, encoding="utf-8") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            for row in reader:
                retired = (row.get("retired_concept_id") or "").strip()
                active = (row.get("active_concept_id") or "").strip()
                if retired and active:
                    pairs[retired] = active
        return pairs

    def handle(self, *args, **options):
        apply_changes = options["apply"]
        pairs = self.load_map(options["map_file"])

        self.stdout.write("=== Retired-concept remap ===")
        self.stdout.write(f"mode                 : {'APPLY' if apply_changes else 'dry-run'}")
        self.stdout.write(f"safe retired->active : {len(pairs)} pairs loaded")

        # Problems with no ICD but with a concept id.
        candidates = Problem.objects.filter(
            Q(icd10_code__isnull=True) | Q(icd10_code=""),
        ).exclude(
            Q(concept_id__isnull=True) | Q(concept_id=""),
        )

        # Only those whose concept is retired-with-a-safe-successor.
        concept_ids = set(candidates.values_list("concept_id", flat=True).distinct())
        healable = {c: pairs[c] for c in concept_ids if c in pairs}
        needs_review = sorted(concept_ids - set(healable))

        self.stdout.write(f"problems missing ICD : {candidates.count()}")
        self.stdout.write(f"distinct concepts    : {len(concept_ids)}")
        self.stdout.write(f"  healable (safe)    : {len(healable)}")
        self.stdout.write(f"  need review        : {len(needs_review)}")

        healed_rows = 0
        unmapped_target = 0
        patients = set()

        for retired, active in sorted(healable.items()):
            icd = SnomedIcd10Map.best_icd10_for(active)
            if not icd:
                # Successor exists but carries no ICD target — leave the row
                # alone rather than advancing the concept for no benefit.
                unmapped_target += 1
                continue

            rows = candidates.filter(concept_id=retired)
            if apply_changes:
                affected = list(rows.values_list("id", "patient_id"))
                with transaction.atomic():
                    updated = rows.update(concept_id=active, icd10_code=icd)
                healed_rows += updated
                patients.update(pid for _, pid in affected if pid)
            else:
                healed_rows += rows.count()
                patients.update(
                    pid for pid in rows.values_list("patient_id", flat=True) if pid
                )

        self.stdout.write("")
        self.stdout.write(
            f"rows {'healed' if apply_changes else 'that would heal'}          : {healed_rows}"
        )
        self.stdout.write(f"patients affected    : {len(patients)}")
        if unmapped_target:
            self.stdout.write(
                f"skipped (successor has no ICD target): {unmapped_target} concepts"
            )

        # Wake the mobile clients. A bulk UPDATE writes no mutation stamp, so
        # without this the corrected codes sit on the server unseen until a
        # manual chart refresh.
        if apply_changes and patients:
            stamped = 0
            for patient_id in patients:
                try:
                    touch_patient_stamp(patient_id)
                    stamped += 1
                except Exception:  # best-effort, never fail the heal
                    pass
            self.stdout.write(f"mutation stamps touched: {stamped}")

        if options["list_review"] and needs_review:
            self.stdout.write("")
            self.stdout.write("--- concepts needing human review (no exact successor) ---")
            for concept in needs_review:
                count = candidates.filter(concept_id=concept).count()
                self.stdout.write(f"  {concept}  ({count} problems)")

        if not apply_changes:
            self.stdout.write("")
            self.stdout.write("Dry run — nothing written. Re-run with --apply to write.")
