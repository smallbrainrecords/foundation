
from .models import Encounter, EncounterEvent
from .models import EncounterProblemRecord


def op_add_event(physician, patient, event_summary, problem=None):

    latest_encounter = Encounter.objects.filter(
        physician=physician,
        patient=patient).order_by('-id')

    if latest_encounter.exists():
        latest_encounter = latest_encounter[0]

        if latest_encounter.is_active():

            # Save Encounter Event
            encounter_event = EncounterEvent(
                encounter=latest_encounter,
                summary=event_summary)
            encounter_event.save()

            # Add Problem Record if any
            if problem:
                try:
                    EncounterProblemRecord.objects.get(
                        encounter=latest_encounter, problem=problem)
                except EncounterProblemRecord.DoesNotExist:
                    EncounterProblemRecord.objects.create(
                        encounter=latest_encounter, problem=problem)

    return True
