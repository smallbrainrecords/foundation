import csv
from django.core.management.base import BaseCommand
from emr.models import SnomedIcd10Map


class Command(BaseCommand):
    help = 'Ingest the NLM SNOMED CT to ICD-10-CM Extended Map RefSet TSV into SnomedIcd10Map'

    def add_arguments(self, parser):
        parser.add_argument('--mapfile', type=str, required=True, help='Path to the Extended Map RefSet TSV file')

    def handle(self, *args, **options):
        file_path = options['mapfile']
        self.stdout.write(f'Loading ICD-10 map from {file_path}...')

        batch = []
        total_count = 0
        skipped = 0

        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            next(reader)  # Skip header

            for row in reader:
                active = row[2]
                snomed_id = row[5]
                map_group = row[6]
                map_priority = row[7]
                map_advice = row[9]
                map_target = row[10]

                if active != '1' or not map_target.strip():
                    skipped += 1
                    continue

                batch.append(SnomedIcd10Map(
                    snomed_concept_id=snomed_id,
                    icd10_code=map_target.strip(),
                    map_advice=map_advice if map_advice else None,
                    map_group=int(map_group),
                    map_priority=int(map_priority),
                ))

                if len(batch) >= 5000:
                    SnomedIcd10Map.objects.bulk_create(batch, ignore_conflicts=True)
                    total_count += len(batch)
                    self.stdout.write(f'Processed {total_count} mappings...')
                    batch = []

            if batch:
                SnomedIcd10Map.objects.bulk_create(batch, ignore_conflicts=True)
                total_count += len(batch)

        self.stdout.write(self.style.SUCCESS(
            f'Finished: {total_count} mappings loaded, {skipped} rows skipped (inactive or no ICD-10 target).'
        ))
