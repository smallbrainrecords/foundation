"""Dump all Encounter IDs as a single JSON array. Used for ID-set
reconciliation between legacy and smallbrain-db during the 2026-06 migration.

Writes to a local file or gs:// URI to avoid Cloud Logging stdout truncation
for large lists."""
import json
import os
import tempfile

from django.core.management.base import BaseCommand

from emr.models import Encounter


class Command(BaseCommand):
    help = "Write all Encounter IDs as JSON to --output (file path or gs:// URI)."

    def add_arguments(self, parser):
        parser.add_argument("--output", type=str, default=None,
                            help="Local path or gs://bucket/path.json. Required.")

    def handle(self, *args, **options):
        output = options["output"]
        if not output:
            raise SystemExit("--output is required")

        ids = sorted(Encounter.objects.values_list("id", flat=True))

        is_gcs = output.startswith("gs://")
        if is_gcs:
            tmp = tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".json", dir="/tmp"
            )
            write_path = tmp.name
            tmp.close()
        else:
            write_path = output

        with open(write_path, "w") as f:
            json.dump(ids, f)

        self.stdout.write(f"Wrote {len(ids)} ids to {write_path}")

        if is_gcs:
            from google.cloud import storage as _gcs
            without_scheme = output[len("gs://"):]
            bucket_name, _, object_path = without_scheme.partition("/")
            _client = _gcs.Client()
            _client.bucket(bucket_name).blob(object_path).upload_from_filename(
                write_path, content_type="application/json"
            )
            self.stdout.write(f"Uploaded -> {output}")
            try:
                os.unlink(write_path)
            except OSError:
                pass
