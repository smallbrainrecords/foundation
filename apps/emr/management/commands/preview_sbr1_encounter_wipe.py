"""Preview (read-only) the SBR1-created encounter wipe.

Identifies smallbrain-db's SBR1-iOS-created encounters via client_uuid IS NOT NULL
(legacy rows have client_uuid=NULL since the column was added later). Reports
what would be deleted plus the cascade counts. No DB changes.
"""
import json

from django.core.management.base import BaseCommand

from emr.models import (
    Encounter,
    EncounterEvent,
    EncounterProblemRecord,
    EncounterTodoRecord,
    EncounterObservationValue,
)


class Command(BaseCommand):
    help = "Preview the encounters that would be wiped, with cascade row counts."

    def handle(self, *args, **options):
        sbr1 = Encounter.objects.exclude(client_uuid__isnull=True)
        ids = list(sbr1.values_list("id", flat=True))

        if not ids:
            self.stdout.write(json.dumps({"sbr1_encounters": 0, "note": "Nothing matches client_uuid IS NOT NULL"}, indent=2))
            return

        starttimes = sbr1.values_list("starttime", flat=True)
        ev_count = EncounterEvent.objects.filter(encounter_id__in=ids).count()
        epr_count = EncounterProblemRecord.objects.filter(encounter_id__in=ids).count()
        etr_count = EncounterTodoRecord.objects.filter(encounter_id__in=ids).count()
        eov_count = EncounterObservationValue.objects.filter(encounter_id__in=ids).count()

        out = {
            "sbr1_encounter_count": len(ids),
            "sbr1_encounter_ids_min": min(ids),
            "sbr1_encounter_ids_max": max(ids),
            "sbr1_starttime_min": str(min(starttimes)),
            "sbr1_starttime_max": str(max(starttimes)),
            "cascade_EncounterEvent": ev_count,
            "cascade_EncounterProblemRecord": epr_count,
            "cascade_EncounterTodoRecord": etr_count,
            "cascade_EncounterObservationValue": eov_count,
            "ids_sample_first10": sorted(ids)[:10],
            "ids_sample_last10": sorted(ids)[-10:],
        }
        self.stdout.write(json.dumps(out, indent=2, default=str))
