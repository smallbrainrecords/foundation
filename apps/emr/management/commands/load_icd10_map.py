"""Replace the SNOMED CT -> ICD-10-CM map table with the bundled map.

    python manage.py load_icd10_map            # dry run: report, write nothing
    python manage.py load_icd10_map --apply    # replace the table

The table is REPLACED, never added to, and only from a file built by
`scripts/build_icd_data.py` (default: the one shipped in the image,
`apps/emr/data/snomed_icd10cm_map.tsv.gz`).

Both halves of that sentence are the fix for the 2026-10-06 incident. The
previous version of this command appended whatever rows it was given, from a
raw SNOMED release file, filtering on nothing but `active`. It was pointed at
the release's Full (history) file, so the table ended up holding the WHO ICD-10
map beside the US ICD-10-CM one plus every superseded version of both —
545,178 rows where the current ICD-10-CM map has 257,611 — and
`best_icd10_for` picked a non-billable code for 39% of the concepts the app
offers. Appending also meant a reload could never remove a retired mapping.

Before anything is written the new rows are checked:
  * no duplicate keys, and no concept whose winning rank is tied (a tie makes
    the pick depend on load order);
  * every pick is a billable ICD-10-CM code or a `?` seventh-character
    placeholder, within a small tolerance for a map and code list from
    adjacent releases. A file from the wrong refset fails here by a mile.

HOW the table is replaced matters, and was learned the hard way. The first
version deleted every row and inserted the new ones inside one transaction. On
a laptop that took 12 seconds. On production's db-f1-micro the DELETE alone
took the job's whole 30 minutes (about 300 rows a second), the job was killed,
and the rollback then ran for longer still — during which any scan of the table
crawled. So on MySQL the command now:

  1. builds the new map in a staging table (`<table>_new`, created `LIKE` the
     live one), in small autocommitted batches — inserts into an empty table,
     no deletes, no long transaction;
  2. checks the staging table against the file;
  3. swaps it in with ONE atomic `RENAME TABLE`: readers see the old table or
     the new one, never a mixture and never an empty one.

The table it replaces is kept as `<table>_previous` until the next reload, so
undoing a bad load is a rename back, not a restore:

    RENAME TABLE emr_snomedicd10map TO emr_snomedicd10map_bad,
                 emr_snomedicd10map_previous TO emr_snomedicd10map;

Other databases keep the simple delete-and-insert in one transaction.

This is a management command run as a Cloud Run job, not a migration, on
purpose: migrations run on every container boot and race each other on MySQL.
"""
import json
import logging

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from emr.icd_codes import MAP_FILE, billable_codes
from emr.icd_map import (
    MapFileError, file_fingerprint, pick_report, read_bundled_map, table_fingerprint,
)
from emr.models import SnomedIcd10Map

_LOGGER = logging.getLogger('smallbrain.icd_map_load')

# Share of picks allowed to be neither billable nor a `?` placeholder. A map
# and a code list one release apart disagree on a handful of codes; the WHO
# refset disagrees on about a third.
MAX_UNBILLABLE_SHARE = 0.01

INSERT_BATCH = 2000
# How long the swap may wait for the table's metadata lock. A statement that
# is still running against the live table (a killed load rolling back, say)
# holds it; failing here leaves the live table untouched.
SWAP_LOCK_WAIT_SECONDS = 300


class Command(BaseCommand):
    help = 'Replace SnomedIcd10Map with the bundled ICD-10-CM map (dry run unless --apply).'

    def add_arguments(self, parser):
        parser.add_argument('--mapfile', default=MAP_FILE,
                            help='A map file built by scripts/build_icd_data.py (default: the bundled one).')
        parser.add_argument('--apply', action='store_true',
                            help='Replace the table. Without it the command only reports.')
        parser.add_argument('--min-rows', type=int, default=100000,
                            help='Refuse a file with fewer rows than this (a truncated file must not empty the table).')

    def say(self, message):
        self.stdout.write(message)
        self.stdout.flush()

    def handle(self, *args, **options):
        path = options['mapfile']
        try:
            rows, comments = read_bundled_map(path)
        except MapFileError as exc:
            raise CommandError(str(exc))

        self.say('=== Load SNOMED -> ICD-10-CM map ===')
        self.say(f"mode            : {'APPLY' if options['apply'] else 'dry-run'}")
        self.say(f'file            : {path}')
        for comment in comments[:2]:
            self.say(f'                  {comment}')

        billable = billable_codes()
        if billable is None:
            raise CommandError(
                'The billable-code list (icd10cm_billable_codes.txt) is missing, so the '
                'new map cannot be checked. Refusing to load an unchecked map.'
            )

        report = pick_report(rows, billable)
        kinds = report['kinds']
        self.say(f"rows in file    : {len(rows)}  ({report['concepts']} concepts)")
        self.say(f'picks           : {kinds}')

        if len(rows) < options['min_rows']:
            raise CommandError(f"only {len(rows)} rows (minimum {options['min_rows']}); refusing to replace the table")
        if report['duplicates']:
            raise CommandError(f"{len(report['duplicates'])} duplicate keys, e.g. {report['duplicates'][:3]}")
        if report['tied']:
            raise CommandError(
                f"{len(report['tied'])} concepts have a tied top rank (e.g. {report['tied'][:5]}); "
                'their pick would depend on load order'
            )
        other = kinds.get('other', 0)
        if other > MAX_UNBILLABLE_SHARE * report['concepts']:
            raise CommandError(
                f"{other} of {report['concepts']} picks are neither billable nor a ? placeholder. "
                'This is not the ICD-10-CM map, or the code list is from a different release.'
            )

        before = table_fingerprint()
        target = file_fingerprint(rows)
        self.say(f'table now       : {before[0]} rows')
        if before == target:
            self.say(self.style.SUCCESS('The table already matches this file. Nothing to do.'))
            return

        if not options['apply']:
            self.say(f'would replace   : {before[0]} rows -> {target[0]} rows')
            self.say('Dry run — nothing written. Re-run with --apply to replace the table.')
            return

        if connection.vendor == 'mysql':
            method = self.replace_by_swap(rows, target)
        else:
            method = self.replace_in_transaction(rows, target)

        _LOGGER.info(json.dumps({
            'event': 'icd_map_replaced',
            'method': method,
            'file': str(path),
            'source': comments[0] if comments else '',
            'rows_before': before[0],
            'rows_after': target[0],
            'picks': kinds,
        }))
        self.say(self.style.SUCCESS(f'Replaced: {before[0]} rows -> {target[0]} rows.'))

    # ------------------------------------------------------------ MySQL

    def replace_by_swap(self, rows, target):
        """Build the new map beside the live table, then rename it into place."""
        quote = connection.ops.quote_name
        live = SnomedIcd10Map._meta.db_table
        staging, previous = live + '_new', live + '_previous'

        with connection.cursor() as cursor:
            # A staging table left by a run that died is rebuilt from scratch.
            cursor.execute(f'DROP TABLE IF EXISTS {quote(staging)}')
            cursor.execute(f'CREATE TABLE {quote(staging)} LIKE {quote(live)}')

            insert = (
                f'INSERT INTO {quote(staging)} '
                '(snomed_concept_id, icd10_code, map_advice, map_group, map_priority) '
                'VALUES (%s, %s, %s, %s, %s)'
            )
            done = 0
            for start in range(0, len(rows), INSERT_BATCH):
                batch = [
                    (concept, code, advice or None, group, priority)
                    for concept, group, priority, code, advice in rows[start:start + INSERT_BATCH]
                ]
                cursor.executemany(insert, batch)
                done += len(batch)
                if done % 50000 < INSERT_BATCH:
                    self.say(f'staging         : {done} of {len(rows)} rows')

            staged = table_fingerprint(staging)
            if staged != target:
                cursor.execute(f'DROP TABLE IF EXISTS {quote(staging)}')
                raise CommandError(
                    f'the staging table does not match the file ({staged} != {target}); '
                    'it was dropped and the live table was not touched'
                )

            # The previous reload's safety copy goes; this run's takes its name.
            cursor.execute(f'DROP TABLE IF EXISTS {quote(previous)}')
            cursor.execute(f'SET SESSION lock_wait_timeout = {SWAP_LOCK_WAIT_SECONDS}')
            try:
                cursor.execute(
                    f'RENAME TABLE {quote(live)} TO {quote(previous)}, {quote(staging)} TO {quote(live)}'
                )
            except Exception as exc:
                raise CommandError(
                    f'the new map is built in {staging} but could not be swapped in ({exc}). '
                    'The live table is unchanged. Something still holds it — re-run this command.'
                )
        self.say(f'swapped         : the table it replaced is kept as {previous}')
        return 'swap'

    # ------------------------------------------------------------ others

    def replace_in_transaction(self, rows, target):
        with transaction.atomic():
            SnomedIcd10Map.objects.all().delete()
            batch = []
            for concept, group, priority, code, advice in rows:
                batch.append(SnomedIcd10Map(
                    snomed_concept_id=concept, icd10_code=code,
                    map_advice=advice or None, map_group=group, map_priority=priority,
                ))
                if len(batch) >= 5000:
                    SnomedIcd10Map.objects.bulk_create(batch)
                    batch = []
            if batch:
                SnomedIcd10Map.objects.bulk_create(batch)
            after = table_fingerprint()
            if after != target:
                # Raising inside the atomic block rolls the whole replace back.
                raise CommandError(f'table does not match the file after insert ({after} != {target}); rolled back')
        return 'transaction'
