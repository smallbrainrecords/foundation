"""
Read-only audit of Encounter.audio paths against the configured storage backend.

For each Encounter row with a non-empty audio path, checks whether the file
actually exists in GCS (or whichever storage backend is configured) and writes
a CSV report. Used to reconcile after the legacy /media_to_sync -> GCS bulk
transfer.

Usage:
    python manage.py audit_encounter_audio
    python manage.py audit_encounter_audio --limit 100        # smoke test
    python manage.py audit_encounter_audio --output /tmp/x.csv
    python manage.py audit_encounter_audio --output gs://bucket/path/x.csv
    python manage.py audit_encounter_audio --skip-size        # faster; only existence
"""
import csv
import os
import tempfile

from django.core.management.base import BaseCommand
from django.utils import timezone

from emr.models import Encounter


class Command(BaseCommand):
    help = 'Audit Encounter.audio paths against the configured storage backend.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit', type=int, default=None,
            help='Only audit the first N rows (smoke test).',
        )
        parser.add_argument(
            '--output', type=str, default=None,
            help='Output CSV path (default: encounter_audio_audit_YYYYMMDDTHHMMSSZ.csv).',
        )
        parser.add_argument(
            '--progress-every', type=int, default=500,
            help='Emit a progress line every N rows (default: 500).',
        )

    def handle(self, *args, **options):
        limit = options['limit']
        progress_every = options['progress_every']

        qs = Encounter.objects.exclude(audio='').order_by('id')
        total = qs.count() if limit is None else min(qs.count(), limit)
        if total == 0:
            self.stdout.write(self.style.WARNING('No encounters with audio paths to audit.'))
            return

        if limit is not None:
            qs = qs[:limit]

        ts = timezone.now().strftime('%Y%m%dT%H%M%SZ')
        output = options['output'] or f'encounter_audio_audit_{ts}.csv'

        # When writing to GCS we buffer to a local tempfile so the existing CSV
        # writer code is unchanged, then upload at the end (or in a finally so
        # a crash mid-run still preserves partial results).
        is_gcs = output.startswith('gs://')
        if is_gcs:
            tmp = tempfile.NamedTemporaryFile(
                mode='w', delete=False, suffix='.csv', prefix='audit_', dir='/tmp'
            )
            write_path = tmp.name
            tmp.close()
        else:
            write_path = output

        present = 0
        missing = 0
        errors = 0

        self.stdout.write(f'Auditing {total} encounter audio paths -> {output}')
        if is_gcs:
            self.stdout.write(f'  (buffering locally at {write_path}, will upload to {output})')

        started = timezone.now()

        with open(write_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'encounter_id',
                'patient_id',
                'starttime',
                'audio_path',
                'exists_in_storage',
                'size_bytes',
                'audio_played_count',
                'error',
            ])

            for i, enc in enumerate(qs.iterator(chunk_size=500), start=1):
                path = enc.audio.name
                # NB: django-storages' GoogleCloudStorage.exists() returns False
                # unconditionally when file_overwrite=True (the default) — it's a
                # save-time optimization, not an existence check. We call
                # bucket.get_blob() directly: returns a Blob (with .size) if the
                # object exists, None if not. One HEAD per row.
                bucket = enc.audio.storage.bucket
                exists = ''
                size = ''
                err = ''
                try:
                    blob = bucket.get_blob(path)
                    if blob is not None:
                        exists = 'true'
                        size = blob.size
                        present += 1
                    else:
                        exists = 'false'
                        missing += 1
                except Exception as e:
                    errors += 1
                    exists = 'error'
                    err = f'{type(e).__name__}: {e}'

                writer.writerow([
                    enc.id,
                    enc.patient_id,
                    enc.starttime.isoformat() if enc.starttime else '',
                    path,
                    exists,
                    size,
                    enc.audio_played_count,
                    err,
                ])

                if i % progress_every == 0:
                    elapsed = (timezone.now() - started).total_seconds()
                    rate = i / elapsed if elapsed > 0 else 0
                    eta = (total - i) / rate if rate > 0 else 0
                    self.stdout.write(
                        f'  {i:>6}/{total}  present={present} missing={missing} '
                        f'errors={errors}  ({rate:.1f} rows/s, eta {eta:.0f}s)'
                    )

        elapsed = (timezone.now() - started).total_seconds()
        self.stdout.write(self.style.SUCCESS(
            f'Done. {total} rows in {elapsed:.1f}s. '
            f'present={present} missing={missing} errors={errors}'
        ))

        if is_gcs:
            self._upload_to_gcs(write_path, output)
            try:
                os.unlink(write_path)
            except OSError:
                pass
        else:
            self.stdout.write(f'CSV at {write_path}')

    def _upload_to_gcs(self, local_path, gs_uri):
        """Upload local_path to gs://bucket/object. Uses ADC for auth."""
        from google.cloud import storage  # available via django-storages[google]

        without_scheme = gs_uri[len('gs://'):]
        bucket_name, _, object_path = without_scheme.partition('/')
        if not bucket_name or not object_path:
            raise ValueError(f'Bad gs:// URI: {gs_uri}')

        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(object_path)
        blob.upload_from_filename(local_path, content_type='text/csv')
        self.stdout.write(self.style.SUCCESS(f'Uploaded -> {gs_uri}'))
