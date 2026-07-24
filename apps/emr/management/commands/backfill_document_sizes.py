"""Backfill Document.file_size from storage metadata (one-time, 2026-07-23).

`file_size` was added so document list serializers stop calling
`doc.document.size` per row — with GCS storage that is a live metadata
round-trip per document, which made the unassigned-pool list (~2.3s at
~100 rows) and the patient_full documents section (1.5–7.7s) scale
linearly with document count (~24ms/row observed in prod request logs).
New uploads write the column at creation; this command fills legacy rows.

Only rows with `file_size IS NULL` and a non-empty file reference are
touched, so re-running is safe (idempotent) and a completed backfill is a
fast no-op. Rows whose storage object is missing are reported and left
NULL — the serializer fallback (`mobile_api._document_file_size`) returns
0 for them without erroring, and `audit_doc_files` remains the deeper
missing-blob audit.

Usage:
    python manage.py backfill_document_sizes            # dry run (counts only)
    python manage.py backfill_document_sizes --apply    # stat storage + write

Dry run deliberately does NOT stat storage (it would take as long as the
real pass); it only reports how many rows the apply pass would touch.
"""
import time

from django.core.management.base import BaseCommand
from django.db.models import Q

from emr.models import Document


class Command(BaseCommand):
    help = "Backfill Document.file_size for rows created before the column existed."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Stat storage and write sizes. Without it, report counts only.",
        )

    def handle(self, *args, **options):
        apply = options["apply"]

        candidates = Document.objects.filter(file_size__isnull=True).exclude(
            Q(document__isnull=True) | Q(document=""),
        )
        no_file = Document.objects.filter(file_size__isnull=True).filter(
            Q(document__isnull=True) | Q(document=""),
        ).count()
        total = candidates.count()

        self.stdout.write("=== Document.file_size backfill ===")
        self.stdout.write(f"mode                    : {'APPLY' if apply else 'dry-run'}")
        self.stdout.write(f"rows needing backfill   : {total}")
        self.stdout.write(f"rows with no file (skip): {no_file}")

        if not apply:
            self.stdout.write("Dry run — nothing written. Use --apply to write.")
            return

        updated = 0
        missing_blob = 0
        started = time.monotonic()
        pending = []

        def flush():
            nonlocal updated
            if pending:
                Document.objects.bulk_update(pending, ["file_size"], batch_size=500)
                updated += len(pending)
                pending.clear()
                elapsed = time.monotonic() - started
                self.stdout.write(f"  ...{updated}/{total} ({elapsed:.0f}s)")

        # .iterator() keeps memory flat; one storage stat per row, writes
        # batched 500 at a time. The stats dominate (~24ms each against
        # GCS), so a full prod pass is ~25 min — run the Cloud Run job
        # with a 90m task-timeout. A timeout or crash mid-pass is safe:
        # only NULL rows are candidates, so re-running resumes where it
        # stopped.
        for doc in candidates.only("id", "document", "file_size").iterator(chunk_size=500):
            try:
                doc.file_size = doc.document.size
            except Exception:
                # Missing/unreadable storage object: leave NULL so the row
                # stays visible to re-runs and to audit_doc_files.
                missing_blob += 1
                continue
            pending.append(doc)
            if len(pending) >= 500:
                flush()
        flush()

        elapsed = time.monotonic() - started
        self.stdout.write(f"rows updated            : {updated}")
        self.stdout.write(f"missing storage objects : {missing_blob}")
        self.stdout.write(f"elapsed                 : {elapsed:.1f}s")
