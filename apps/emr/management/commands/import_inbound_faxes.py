"""`import_inbound_faxes` — one import pass of the clinic line's received faxes
into the unassigned pool (emr.inbound_fax), for a Cloud Run job, which Cloud
Scheduler can run on a schedule so faxes keep arriving when no staff Mac is
open. RingCentral keeps only about a week of received faxes, so the schedule
is what makes a holiday closure safe.

    manage.py import_inbound_faxes [--batch 25] [--delete-batch 20] [--dry-run]

Prints the pass summary as one JSON line (counts only) and exits non-zero
when RingCentral's list could not be read. `--dry-run` reads the list and
says how many faxes would be fetched, downloading and writing nothing — the
way to check the settings before turning the import on.

The job also moves up to `--delete-batch` faxes that are stored here to
RingCentral's Deleted folder (owner, 2026-11-18); `--delete-batch 0` skips
that, and a dry run only counts them.
"""
import json

from django.core.management.base import BaseCommand, CommandError

from emr import inbound_fax, ringcentral_fax


class Command(BaseCommand):
    help = "Import the clinic line's newly received faxes into the unassigned pool."

    def add_arguments(self, parser):
        parser.add_argument('--batch', type=int, default=25)
        parser.add_argument('--delete-batch', type=int, default=inbound_fax.DELETE_PER_RUN)
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        try:
            summary = inbound_fax.import_new_faxes(
                batch=max(1, options['batch']), trigger='job', dry_run=options['dry_run'],
                delete_batch=max(0, options['delete_batch']))
        except (ringcentral_fax.FaxError, ringcentral_fax.FaxNotConfigured) as error:
            self.stdout.write(json.dumps({'kind': 'inbound_fax_import', 'ok': False, 'reason': str(error)[:300]}))
            raise CommandError('RingCentral could not be read.')
        self.stdout.write(json.dumps(dict(kind='inbound_fax_import', ok=True, dry_run=options['dry_run'], **summary)))
