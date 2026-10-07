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

The delete and the insert are ONE transaction, so `best_icd10_for` reads the
old rows until the commit and a failure part-way leaves the table as it was.

This is a management command run as a Cloud Run job, not a migration, on
purpose: migrations run on every container boot and race each other on MySQL.
"""
import json
import logging

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

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


class Command(BaseCommand):
    help = 'Replace SnomedIcd10Map with the bundled ICD-10-CM map (dry run unless --apply).'

    def add_arguments(self, parser):
        parser.add_argument('--mapfile', default=MAP_FILE,
                            help='A map file built by scripts/build_icd_data.py (default: the bundled one).')
        parser.add_argument('--apply', action='store_true',
                            help='Replace the table. Without it the command only reports.')
        parser.add_argument('--min-rows', type=int, default=100000,
                            help='Refuse a file with fewer rows than this (a truncated file must not empty the table).')

    def handle(self, *args, **options):
        path = options['mapfile']
        try:
            rows, comments = read_bundled_map(path)
        except MapFileError as exc:
            raise CommandError(str(exc))

        self.stdout.write('=== Load SNOMED -> ICD-10-CM map ===')
        self.stdout.write(f"mode            : {'APPLY' if options['apply'] else 'dry-run'}")
        self.stdout.write(f'file            : {path}')
        for comment in comments[:2]:
            self.stdout.write(f'                  {comment}')

        billable = billable_codes()
        if billable is None:
            raise CommandError(
                'The billable-code list (icd10cm_billable_codes.txt) is missing, so the '
                'new map cannot be checked. Refusing to load an unchecked map.'
            )

        report = pick_report(rows, billable)
        kinds = report['kinds']
        self.stdout.write(f"rows in file    : {len(rows)}  ({report['concepts']} concepts)")
        self.stdout.write(f'picks           : {kinds}')

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
        self.stdout.write(f'table now       : {before[0]} rows')
        if before == target:
            self.stdout.write(self.style.SUCCESS('The table already matches this file. Nothing to do.'))
            return

        if not options['apply']:
            self.stdout.write(f'would replace   : {before[0]} rows -> {target[0]} rows')
            self.stdout.write('Dry run — nothing written. Re-run with --apply to replace the table.')
            return

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

        _LOGGER.info(json.dumps({
            'event': 'icd_map_replaced',
            'file': str(path),
            'source': comments[0] if comments else '',
            'rows_before': before[0],
            'rows_after': target[0],
            'picks': kinds,
        }))
        self.stdout.write(self.style.SUCCESS(f'Replaced: {before[0]} rows -> {target[0]} rows.'))
