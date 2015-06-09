
from django.contrib.auth.models import User

from .models import Encounter, EncounterEvent



def op_add_event(physician, patient, event_summary):

    latest_encounter = Encounter.objects.filter(
        physician=physician,
        patient=patient).order_by('-id')

    if latest_encounter.exists():
        latest_encounter = latest_encounter[0]
        if latest_encounter.is_active() == True:

            encounter_event = EncounterEvent(
                encounter=latest_encounter,
                summary=event_summary)
            encounter_event.save()

	return True
