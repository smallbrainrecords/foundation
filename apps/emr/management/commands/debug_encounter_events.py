"""Debug: print EncounterEvent rows for a specific encounter."""
from django.core.management.base import BaseCommand
from emr.models import EncounterEvent, Encounter


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--encounter-id", type=int, required=True)

    def handle(self, *args, **options):
        eid = options["encounter_id"]
        try:
            enc = Encounter.objects.get(id=eid)
            self.stdout.write(f"Encounter {eid}: starttime={enc.starttime} stoptime={enc.stoptime}")
        except Encounter.DoesNotExist:
            self.stdout.write(f"Encounter {eid} NOT FOUND")
            return

        for e in EncounterEvent.objects.filter(encounter_id=eid).order_by("id"):
            self.stdout.write(f"  event id={e.id} datetime={e.datetime} timestamp={e.timestamp} summary={e.summary[:60]}")
