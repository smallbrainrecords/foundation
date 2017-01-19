from emr.models import Encounter, EncounterEvent


def op_medication_event(actor, patient, summary):
    """
    Log medication event to encounter & pinned problem \n
    Addition: Added medication {medication_name_and_link_to_medication_page} \n
    Dosage change: {medication_name__and_dosage_old} was changed to {medication_name__and_dosage_new} \n
    Note change: {medication_name} was changed from {medication_note_text_old} to {medication_note_text_new} \n
    Status change: {medication_name} active/inactive \n
    :param actor:
    :param patient:
    :param summary:
    :return:
    """
    latest_encounter = Encounter.objects.filter(physician=actor, patient=patient).order_by('-id')

    if latest_encounter.exists():
        latest_encounter = latest_encounter[0]

        if latest_encounter.is_active():
            encounter_event = EncounterEvent(encounter=latest_encounter, summary=summary)
            encounter_event.save()
    pass
