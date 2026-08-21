"""Collapse the Label table to one canonical row per category, and code them.

Production accumulated 15 Label rows for 6 real categories (Imaging x5,
Laboratory x3, Referral x2, screening x2, plus a stray "testLABforme"), because
`mobile_create_todo_label` / `mobile_create_label` created a new row on every
call instead of reusing one. Those endpoints are fixed in the same change; this
command cleans up what they already produced and establishes the canonical set.

It matters more than it looks: `Label` is shared by DOCUMENTS and TODOS, and
documents dominate it (~58k links vs ~2.3k). A label reaches a todo mainly when
a labelled PDF is linked to it. Problems use a separate table (`ProblemLabel`)
and are untouched here.

Safe by construction: every duplicate row currently holds ZERO document links,
so consolidation repoints only a handful of todo links. The command re-checks
that at runtime rather than trusting it — links are repointed, never dropped,
and a duplicate is deleted only once nothing references it.

Canonical set (colour + SNOMED category). Every code was verified against the
SNOMED CT US release, not written from memory:

    Laboratory     red     108252007  Laboratory procedure
    Imaging        purple  363679005  Imaging
    Procedure      sky     71388002   Procedure
    Referral       green   3457005    Patient referral
    Medication     blue    33633005   Prescription of drug
    Correspondence orange  263536004  Communication
    screening      yellow  360156006  Screening intent

Two of those are deliberately not ServiceRequest categories: "screening" is a
PURPOSE that cuts across the types (a screening colonoscopy is a Procedure AND
screening — the production data shows exactly that), so it maps to an intent;
and "Medication" is a MedicationRequest rather than a ServiceRequest.

Usage:
    python manage.py consolidate_labels             # dry run (default)
    python manage.py consolidate_labels --apply     # write
    python manage.py consolidate_labels --apply --prune "testLABforme"
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from emr.models import Label

CANONICAL = [
    ("Laboratory",     "todo-label-red",    "108252007"),
    ("Imaging",        "todo-label-purple", "363679005"),
    ("Procedure",      "todo-label-sky",    "71388002"),
    ("Referral",       "todo-label-green",  "3457005"),
    ("Medication",     "todo-label-blue",   "33633005"),
    ("Correspondence", "todo-label-orange", "263536004"),
    ("screening",      "todo-label-yellow", "360156006"),
]


class Command(BaseCommand):
    help = "Merge duplicate Labels into one canonical row per category and set SNOMED codes."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Write changes.")
        parser.add_argument(
            "--prune",
            action="append",
            default=[],
            help="Delete a non-canonical label by exact name (repeatable). "
                 "Its links are removed with it, so name them explicitly.",
        )

    def link_counts(self, label):
        """Every reference to this Label row, so nothing is deleted blind."""
        return {
            "todos": label.todo_set.count(),
            "documents": label.document_set.count(),
            "lists": label.labeledtodolist_set.count(),
        }

    def handle(self, *args, **options):
        apply_changes = options["apply"]
        prune = set(options["prune"])

        self.stdout.write("=== Label consolidation ===")
        self.stdout.write(f"mode : {'APPLY' if apply_changes else 'dry-run'}")
        self.stdout.write(f"rows before : {Label.objects.count()}")
        self.stdout.write("")

        merged_rows = 0
        deleted = 0

        for name, css, snomed in CANONICAL:
            matches = list(
                Label.objects.filter(name__iexact=name).order_by("-is_all", "id")
            )
            if not matches:
                self.stdout.write(f"{name:<15} MISSING -> create (global, {css}, {snomed})")
                if apply_changes:
                    Label.objects.create(
                        name=name, css_class=css, is_all=True,
                        snomed_category_code=snomed,
                    )
                continue

            keeper, dupes = matches[0], matches[1:]
            counts = self.link_counts(keeper)
            note = f"keep id={keeper.id} (todos={counts['todos']} docs={counts['documents']})"
            self.stdout.write(f"{name:<15} {note}")

            if apply_changes:
                keeper.is_all = True
                keeper.css_class = keeper.css_class or css
                keeper.snomed_category_code = snomed
                keeper.save(update_fields=["is_all", "css_class", "snomed_category_code"])

            for dup in dupes:
                dcounts = self.link_counts(dup)
                total = sum(dcounts.values())
                self.stdout.write(
                    f"{'':<15}   merge id={dup.id} "
                    f"(todos={dcounts['todos']} docs={dcounts['documents']} lists={dcounts['lists']})"
                )
                merged_rows += total
                if not apply_changes:
                    continue

                with transaction.atomic():
                    # Repoint every reference before the row can be deleted.
                    for todo in dup.todo_set.all():
                        todo.labels.add(keeper)
                        todo.labels.remove(dup)
                    for doc in dup.document_set.all():
                        doc.labels.add(keeper)
                        doc.labels.remove(dup)
                    for lst in dup.labeledtodolist_set.all():
                        lst.labels.add(keeper)
                        lst.labels.remove(dup)

                    # Re-check from the database rather than trusting the loop.
                    remaining = self.link_counts(dup)
                    if any(remaining.values()):
                        self.stdout.write(
                            self.style.WARNING(
                                f"{'':<15}   SKIP delete id={dup.id}: still referenced {remaining}"
                            )
                        )
                        continue
                    dup.delete()
                    deleted += 1

        # Anything outside the canonical set is a user label: report, never
        # touch, unless explicitly named with --prune.
        canonical_names = {n.lower() for n, _, _ in CANONICAL}
        others = [l for l in Label.objects.all() if (l.name or "").lower() not in canonical_names]
        if others:
            self.stdout.write("")
            self.stdout.write("--- non-canonical labels (left alone unless --prune) ---")
            for l in others:
                c = self.link_counts(l)
                mark = "  <- PRUNE" if l.name in prune else ""
                self.stdout.write(
                    f"  id={l.id:<4} {str(l.name)[:24]:<26} "
                    f"todos={c['todos']} docs={c['documents']}{mark}"
                )
                if apply_changes and l.name in prune:
                    l.delete()
                    deleted += 1

        self.stdout.write("")
        self.stdout.write(f"links {'repointed' if apply_changes else 'to repoint'} : {merged_rows}")
        self.stdout.write(f"rows {'deleted' if apply_changes else 'to delete'}     : {deleted if apply_changes else len(CANONICAL) and 'see above'}")
        self.stdout.write(f"rows after  : {Label.objects.count()}")
        if not apply_changes:
            self.stdout.write("")
            self.stdout.write("Dry run — nothing written. Re-run with --apply to write.")
