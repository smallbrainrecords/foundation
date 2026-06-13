"""Write all auth_user IDs as JSON list (to local path or gs:// URI)."""
import json
import os
import tempfile

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Write all auth_user IDs as JSON to --output."

    def add_arguments(self, parser):
        parser.add_argument("--output", type=str, required=True)

    def handle(self, *args, **options):
        ids = sorted(User.objects.values_list("id", flat=True))
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

        self.stdout.write(f"Wrote {len(ids)} ids to {write_path}")

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
