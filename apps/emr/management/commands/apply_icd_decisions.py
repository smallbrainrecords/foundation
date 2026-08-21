"""Apply the clinician-reviewed ICD-10 mappings for concepts SNOMED can't map.

After `remap_retired_concepts` healed every retired concept with an EXACT
successor, 177 concepts remained that no automatic rule can safely resolve:
either SNOMED offers only ambiguous successors ("possibly equivalent to"), or
it offers none at all. Those were reviewed by the practice owner in a local
mapping tool and the result is bundled here as
`apps/emr/data/icd_concept_decisions.json`.

This command applies that reviewed file. It is deliberately NOT a rule — every
mapping in it is a recorded human decision, which is the whole point: the codes
land on billing documents, so a guess is worse than a blank.

What it does per decision: set `icd10_code` on the patient's Problem rows that
carry the decided `concept_id` AND currently have no code. It does NOT advance
`concept_id` (unlike `remap_retired_concepts`) because the decision recorded is
about the ICD, not about which SNOMED successor was intended — several of these
concepts have no successor at all.

Existing codes are never overwritten: a row that already has an ICD came from
somewhere else (the live auto-assign, the backfill, a staged CommonProblem) and
this file's author was reviewing the BLANK ones.

Like the other data-heal commands it touches each affected patient's
`PatientMutationStamp`, so the mobile `/changed` poll notices and the clinic
Macs refresh instead of holding a stale blank code.

The file also carries a `cancelled` list — concepts the owner reviewed and
deliberately left uncoded (no appropriate ICD exists, e.g. "Q wave normal", or
a procedure rather than a diagnosis). Those are reported, never written, so the
record of "we looked at this and chose nothing" survives.

Usage:
    python manage.py apply_icd_decisions              # dry run (default)
    python manage.py apply_icd_decisions --apply      # write
"""
import json
import os

from django.core.management.base import BaseCommand
from django.db.models import Q

from emr.models import Problem
from emr.mutation_stamp import touch_patient_stamp

DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "icd_concept_decisions.json",
)


class Command(BaseCommand):
    help = "Apply the reviewed ICD-10 mappings for concepts with no safe automatic successor."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Write the codes. Without this flag the command only reports.",
        )
        parser.add_argument(
            "--decisions",
            default=DATA_FILE,
            help="Override the bundled decisions file.",
        )

    def handle(self, *args, **options):
        apply_changes = options["apply"]
        with open(options["decisions"], encoding="utf-8") as handle:
            doc = json.load(handle)

        decisions = doc.get("decisions", [])
        cancelled = doc.get("cancelled", [])

        self.stdout.write("=== Apply reviewed ICD-10 decisions ===")
        self.stdout.write(f"mode                 : {'APPLY' if apply_changes else 'dry-run'}")
        self.stdout.write(f"reviewed on          : {doc.get('generated', 'unknown')}")
        self.stdout.write(f"decisions in file    : {len(decisions)}")
        self.stdout.write(f"deliberately uncoded : {len(cancelled)}")

        written = 0
        patients = set()
        no_rows = 0
        already_coded = 0

        for entry in decisions:
            concept = entry["concept"]
            code = entry["icd"]

            uncoded = Problem.objects.filter(
                Q(icd10_code__isnull=True) | Q(icd10_code=""),
                concept_id=concept,
            )
            count = uncoded.count()
            if not count:
                # Either healed by another pass since the review, or the rows
                # changed. Not an error — just nothing left to do.
                no_rows += 1
                already_coded += Problem.objects.filter(concept_id=concept).count()
                continue

            if apply_changes:
                patients.update(
                    pid for pid in uncoded.values_list("patient_id", flat=True) if pid
                )
                written += uncoded.update(icd10_code=code)
            else:
                patients.update(
                    pid for pid in uncoded.values_list("patient_id", flat=True) if pid
                )
                written += count

        self.stdout.write("")
        self.stdout.write(
            f"rows {'coded' if apply_changes else 'that would code'}    : {written}"
        )
        self.stdout.write(f"patients affected    : {len(patients)}")
        if no_rows:
            self.stdout.write(
                f"decisions with nothing left to code: {no_rows} "
                f"(already carry a code from another pass)"
            )

        if apply_changes and patients:
            stamped = 0
            for patient_id in patients:
                try:
                    touch_patient_stamp(patient_id)
                    stamped += 1
                except Exception:  # best-effort; never fail a completed heal
                    pass
            self.stdout.write(f"mutation stamps touched: {stamped}")

        if cancelled:
            self.stdout.write("")
            self.stdout.write("--- reviewed and deliberately left uncoded ---")
            for entry in cancelled:
                self.stdout.write(f"  {entry['concept']:<16} {entry['name'][:52]}")

        if not apply_changes:
            self.stdout.write("")
            self.stdout.write("Dry run — nothing written. Re-run with --apply to write.")
