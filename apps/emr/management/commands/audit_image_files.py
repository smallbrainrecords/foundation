"""Audit PatientImage file paths against GCS."""
import csv
import os
import tempfile

from django.core.management.base import BaseCommand
from django.utils import timezone

from emr.models import PatientImage


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--output", type=str, required=True)
        parser.add_argument("--limit", type=int, default=None)

    def handle(self, *args, **options):
        limit = options["limit"]
        output = options["output"]
        is_gcs = output.startswith("gs://")

        qs = PatientImage.objects.exclude(image="").order_by("id")
        if limit:
            qs = qs[:limit]
        total = qs.count()
        if total == 0:
            self.stdout.write("nothing to audit")
            return

        if is_gcs:
            tmp = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv", dir="/tmp")
            write_path = tmp.name
            tmp.close()
        else:
            write_path = output

        present = missing = errors = 0
        self.stdout.write(f"Auditing {total} image paths -> {output}")
        started = timezone.now()

        with open(write_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["image_id", "patient_id", "problem_id", "datetime", "image_path", "exists_in_storage", "size_bytes", "error"])
            for i, im in enumerate(qs.iterator(chunk_size=500), start=1):
                path = im.image.name
                bucket = im.image.storage.bucket
                try:
                    blob = bucket.get_blob(path)
                    if blob is not None:
                        present += 1
                        w.writerow([im.id, im.patient_id, im.problem_id, im.datetime.isoformat() if im.datetime else "", path, "true", blob.size, ""])
                    else:
                        missing += 1
                        w.writerow([im.id, im.patient_id, im.problem_id, im.datetime.isoformat() if im.datetime else "", path, "false", "", ""])
                except Exception as e:
                    errors += 1
                    w.writerow([im.id, im.patient_id, im.problem_id, im.datetime.isoformat() if im.datetime else "", path, "error", "", f"{type(e).__name__}: {e}"])

                if i % 500 == 0:
                    elapsed = (timezone.now() - started).total_seconds()
                    rate = i / elapsed if elapsed > 0 else 0
                    eta = (total - i) / rate if rate > 0 else 0
                    self.stdout.write(f"  {i:>6}/{total}  present={present} missing={missing} ({rate:.1f}/s eta {eta:.0f}s)")

        elapsed = (timezone.now() - started).total_seconds()
        self.stdout.write(self.style.SUCCESS(f"Done. {total} rows in {elapsed:.1f}s. present={present} missing={missing} errors={errors}"))

        if is_gcs:
            from google.cloud import storage as _gcs
            without_scheme = output[len("gs://"):]
            bucket_name, _, object_path = without_scheme.partition("/")
            _gcs.Client().bucket(bucket_name).blob(object_path).upload_from_filename(write_path, content_type="text/csv")
            self.stdout.write(f"Uploaded -> {output}")
            try:
                os.unlink(write_path)
            except OSError:
                pass
