import csv
from django.core.management.base import BaseCommand
from emr.models import SnomedConcept, SnomedRelationship

class Command(BaseCommand):
    help = 'Ingest SNOMED CT US Edition RF2 Snapshot files into the database'

    def add_arguments(self, parser):
        parser.add_argument('--concepts', type=str, required=True, help='Path to the concept TSV file')
        parser.add_argument('--relationships', type=str, required=True, help='Path to the relationship TSV file')

    def handle(self, *args, **options):
        concept_path = options['concepts']
        relationship_path = options['relationships']

        self.load_concepts(concept_path)
        self.load_relationships(relationship_path)

        self.stdout.write(self.style.SUCCESS('Successfully loaded SNOMED data'))

    def load_concepts(self, file_path):
        self.stdout.write(f'Loading concepts from {file_path}...')
        batch = []
        count = 0
        total_count = 0
        
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            next(reader)  # Skip header row
            
            for row in reader:
                # Column indexes: id [0], effectiveTime [1], active [2]
                concept_id = row[0]
                active = row[2]

                if active == "1":
                    batch.append(SnomedConcept(
                        concept_id=concept_id,
                        active=True
                    ))
                    count += 1
                
                if len(batch) >= 5000:
                    SnomedConcept.objects.bulk_create(batch, ignore_conflicts=True)
                    total_count += len(batch)
                    self.stdout.write(f'Processed {total_count} concepts...')
                    batch = []

            if batch:
                SnomedConcept.objects.bulk_create(batch, ignore_conflicts=True)
                total_count += len(batch)

        self.stdout.write(self.style.SUCCESS(f'Finished loading {total_count} active concepts.'))

    def load_relationships(self, file_path):
        self.stdout.write(f'Loading relationships from {file_path}...')
        batch = []
        count = 0
        total_count = 0
        
        # We need to ensure we only load relationships for concepts that exist if we weren't using ignore_conflicts
        # but the prompt says just load them. Relationships filtering: active == "1" AND typeId == "116680003"
        
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            next(reader)  # Skip header row
            
            for row in reader:
                # Column indexes: id [0], effectiveTime [1], active [2], moduleId [3], 
                # sourceId [4], destinationId [5], relationshipGroup [6], typeId [7]
                rel_id = row[0]
                active = row[2]
                source_id = row[4]
                destination_id = row[5]
                type_id = row[7]

                if active == "1" and type_id == "116680003":
                    batch.append(SnomedRelationship(
                        id=rel_id,
                        active=True,
                        source_id=source_id,
                        destination_id=destination_id,
                        type_id=type_id
                    ))
                    count += 1
                
                if len(batch) >= 5000:
                    SnomedRelationship.objects.bulk_create(batch, ignore_conflicts=True)
                    total_count += len(batch)
                    self.stdout.write(f'Processed {total_count} relationships...')
                    batch = []

            if batch:
                SnomedRelationship.objects.bulk_create(batch, ignore_conflicts=True)
                total_count += len(batch)

        self.stdout.write(self.style.SUCCESS(f'Finished loading {total_count} active "Is a" relationships.'))
