"""Give free-text Problems a SNOMED concept (and therefore an ICD-10) by name.

Field incident 2026-08-24. An order requisition for "take eliquis 5 mg" printed
its diagnosis as bare text — "Deep venous thrombosis (disorder)" with no SNOMED
and no ICD — because that Problem carries `concept_id = ''`. Nothing downstream
can derive a code from nothing, so every earlier fix (the retired-concept remap,
the reviewed decisions, the update guards) was structurally unable to help it.

The tell is the name itself: "Deep venous thrombosis (disorder)" is SNOMED's own
FSN formatting, "(disorder)" suffix and all. A clinician does not type that. It
matches concept 128053003, which the app already offers in its pick list — the
concept simply was never stored. The likely path is the Add Problem panel, where
the "Add Problem" button creates from the typed text with no concept even when a
perfect match is listed in the results right beside it.

Measured across production: **2,075 of 3,208 free-text problems (65%) carry a
name that exactly matches a concept the app offers**, spread over 713 distinct
names — Atrial fibrillation (x15), Paroxysmal atrial fibrillation (x11), Asthma,
Type 2 diabetes, Allergic rhinitis. Healing them takes problem ICD coverage from
roughly 87% to roughly 95%.

MATCHING IS EXACT, CASE-INSENSITIVE, TRIMMED — NEVER FUZZY. These are diagnoses
on billing documents: a near-match is a wrong diagnosis, which is worse than no
code at all. The same reasoning that keeps "possibly equivalent to" out of the
retired-concept remap applies here with more force, because a name collision has
none of SNOMED's editorial review behind it. The bundled map
(`apps/emr/data/snomed_name_to_concept.tsv`) is generated from the app's own
CORE subset, so this can only ever assign a concept the app itself could have
created, and any name mapping to more than one concept is dropped rather than
guessed.

Existing values are never overwritten: only `concept_id` that is empty is
filled, and an existing `icd10_code` is left alone.

Usage:
    python manage.py heal_freetext_problems            # dry run (default)
    python manage.py heal_freetext_problems --apply
    python manage.py heal_freetext_problems --sample 40
"""
import csv
import os

from django.core.management.base import BaseCommand
from django.db.models import Q

from emr.models import Problem, SnomedIcd10Map
from emr.mutation_stamp import touch_patient_stamp

DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "snomed_name_to_concept.tsv",
)


class Command(BaseCommand):
    help = "Match free-text Problems to a SNOMED concept by exact name, and derive the ICD-10."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Write the changes.")
        parser.add_argument(
            "--sample", type=int, default=12,
            help="How many matches to print for review (default 12).",
        )
        parser.add_argument("--map-file", default=DATA_FILE)

    def load_map(self, path):
        names = {}
        with open(path, encoding="utf-8") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                key = (row.get("normalized_name") or "").strip()
                cid = (row.get("concept_id") or "").strip()
                if key and cid:
                    names[key] = cid
        return names

    def handle(self, *args, **options):
        apply_changes = options["apply"]
        names = self.load_map(options["map_file"])

        freetext = Problem.objects.filter(
            Q(concept_id__isnull=True) | Q(concept_id=""),
        )
        total = freetext.count()

        self.stdout.write("=== Free-text problem heal (exact name match) ===")
        self.stdout.write(f"mode                  : {'APPLY' if apply_changes else 'dry-run'}")
        self.stdout.write(f"known names           : {len(names):,}")
        self.stdout.write(f"free-text problems    : {total:,}")

        matched_rows = 0
        coded_rows = 0
        patients = set()
        unmatched_names = {}
        samples = []

        # Group by name so one lookup serves every row sharing it.
        by_name = {}
        for pid, pname, patient_id in freetext.values_list("id", "problem_name", "patient_id"):
            key = (pname or "").strip().lower()
            by_name.setdefault(key, []).append((pid, pname, patient_id))

        for key, rows in by_name.items():
            concept = names.get(key)
            if not concept:
                unmatched_names[key] = len(rows)
                continue
            icd = SnomedIcd10Map.best_icd10_for(concept) or ""
            matched_rows += len(rows)
            if icd:
                coded_rows += len(rows)
            if len(samples) < options["sample"]:
                samples.append((rows[0][1], concept, icd, len(rows)))

            if apply_changes:
                ids = [r[0] for r in rows]
                update = {"concept_id": concept}
                # Never clobber a code that came from somewhere else.
                Problem.objects.filter(id__in=ids).update(**update)
                if icd:
                    Problem.objects.filter(id__in=ids).filter(
                        Q(icd10_code__isnull=True) | Q(icd10_code="")
                    ).update(icd10_code=icd)
                patients.update(r[2] for r in rows if r[2])
            else:
                patients.update(r[2] for r in rows if r[2])

        self.stdout.write("")
        self.stdout.write(f"rows {'matched' if apply_changes else 'that would match'}         : {matched_rows:,}")
        self.stdout.write(f"  of those, gain an ICD : {coded_rows:,}")
        self.stdout.write(f"rows with no name match : {total - matched_rows:,}")
        self.stdout.write(f"patients affected       : {len(patients):,}")

        if samples:
            self.stdout.write("")
            self.stdout.write("--- sample matches ---")
            for name, concept, icd, count in samples:
                self.stdout.write(
                    f"  {str(name)[:44]:<46} -> {concept:<14} {icd or '(no ICD)':<10} x{count}"
                )

        if not apply_changes and unmatched_names:
            top = sorted(unmatched_names.items(), key=lambda kv: -kv[1])[:8]
            self.stdout.write("")
            self.stdout.write("--- most common names with NO exact match (left alone) ---")
            for name, count in top:
                self.stdout.write(f"  {str(name)[:56]:<58} x{count}")

        if apply_changes and patients:
            stamped = 0
            for patient_id in patients:
                try:
                    touch_patient_stamp(patient_id)
                    stamped += 1
                except Exception:
                    pass
            self.stdout.write(f"\nmutation stamps touched : {stamped:,}")

        if not apply_changes:
            self.stdout.write("")
            self.stdout.write("Dry run — nothing written. Re-run with --apply to write.")
