import csv
import os
from django.core.management.base import BaseCommand
from django.db.models import Q
from emr.models import SnomedIcd10Map, Problem

class Command(BaseCommand):
    help = 'Backfill legacy ICD-10 codes for top 500 problems and isolate ambiguous mappings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv',
            type=str,
            required=True,
            help='Path to the top_500_problems.csv file'
        )

    def handle(self, *args, **options):
        csv_file_path = options['csv']
        needs_review_list = []
        mapped_count = 0

        try:
            with open(csv_file_path, mode='r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                # Expected headers: rank, concept_id, problem_name, count
                
                for row in reader:
                    concept_id = row.get('concept_id')
                    problem_name = row.get('problem_name')
                    
                    if not concept_id:
                        continue
                    
                    # Query SnomedIcd10Map for the Concept_ID
                    mappings = SnomedIcd10Map.objects.filter(snomed_concept_id=concept_id)
                    mapping_count = mappings.count()
                    
                    if mapping_count >= 1:
                        # Extract the icd10_code (first mapping is highest priority due to model ordering)
                        icd10_code = mappings.first().icd10_code
                        
                        # Perform a bulk update on the legacy data
                        # Only backfill where icd10_code is missing or empty
                        updated = Problem.objects.filter(
                            Q(icd10_code__isnull=True) | Q(icd10_code=''),
                            concept_id=concept_id
                        ).update(icd10_code=icd10_code)
                        
                        # Print success log to stdout
                        self.stdout.write(f"Mapped {problem_name} to {icd10_code} (Updated {updated} records)")
                        mapped_count += 1
                    else:
                        # Append the row to the manual review list
                        row['Available_Options'] = mapping_count
                        needs_review_list.append(row)

            # Write manual review list to needs_review_problems.csv in project root
            output_file = 'needs_review_problems.csv'
            # Headers: original plus Available_Options
            fieldnames = reader.fieldnames + ['Available_Options']
            
            with open(output_file, mode='w', encoding='utf-8', newline='') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(needs_review_list)
                
            # Final summary
            self.stdout.write(self.style.SUCCESS(
                f"Successfully mapped {mapped_count} problems. "
                f"Wrote {len(needs_review_list)} problems to {output_file}"
            ))

        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"CSV file not found: {csv_file_path}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An error occurred: {str(e)}"))
