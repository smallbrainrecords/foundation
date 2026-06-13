"""List the IDs of encounters identified as SBR1-iOS-created via the
starttime >= 2026-05-01 discriminator. Writes JSON list to --output."""
import json
import os
import tempfile

from django.core.management.base import BaseCommand

from emr.models import Encounter

CUTOFF = "2026-05-01"


class Command(BaseCommand):
    help = "Write SBR1-created encounter IDs (starttime >= 2026-05-01) as JSON."

    def add_arguments(self, parser):
        parser.add_argument("--output", type=str, required=True,
                            help="Local path or gs://bucket/path.json.")

    def handle(self, *args, **options):
        ids = sorted(Encounter.objects.filter(starttime__gte=CUTOFF).values_list("id", flat=True))

        output = options["output"]
        is_gcs = output.startswith("gs://")
        if is_gcs:
            tmp = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json", dir="/tmp")
            write_path = tmp.name
            tmp.close()
        else:
            write_path = output

        with open(write_path, "w") as f:
            json.dump(ids, f)

        self.stdout.write(f"Wrote {len(ids)} SBR1 ids (cutoff {CUTOFF}) to {write_path}")

        if is_gcs:
            from google.cloud import storage as _gcs
            without_scheme = output[len("gs://"):]
            bucket_name, _, object_path = without_scheme.partition("/")
            _gcs.Client().bucket(bucket_name).blob(object_path).upload_from_filename(
                write_path, content_type="application/json"
            )
            self.stdout.write(f"Uploaded -> {output}")
            try:
                os.unlink(write_path)
            except OSError:
                pass
