from emr.models import Encounter, EncounterEvent, ProblemActivity, MedicationPinToProblem, PatientController, Problem


def op_medication_event(medication, actor, patient, summary):
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

    # Add log to pinned problem activity
    problems = medication.problem_set.all()
    for problem in problems:
        activity = ProblemActivity(problem=problem, author=actor, activity=summary)
        activity.save()

    pass


def count_pinned_have_same_medication_concept_id_and_problem_concept_id(actor, medication, problem):
    """
    Finding number of pinned instance having same pair of medication's concept id and problem's concept id
    by the physician
    :param actor:
    :param medication:
    :param problem:
    :return:
    """

    if problem.concept_id is not None and medication.concept_id is not None:
        pinned_instance = MedicationPinToProblem.objects.filter(author=actor.profile).filter(
            medication__concept_id=medication.concept_id).filter(
            problem__concept_id=problem.concept_id)
        return pinned_instance, pinned_instance.count()
    pass


def op_pin_medication_to_problem_for_all_controlled_patient(actor, pinned_instance_set, medication, problem):
    """
    Pin medication to any instance of problem for all the patients associated with that physician.
    :param actor:
    :param pinned_instance_set:
    :param medication:
    :param problem:
    :return:
    """
    controlled_patients = PatientController.objects.filter(physician=actor)
    controlled_patient_id_set = [long(x.patient.id) for x in controlled_patients]
    pinned_instance_id_set = [long(x.problem_id) for x in pinned_instance_set]

    # Filtered out all problem already pinned to this medication
    problems = Problem.objects.filter(concept_id=problem.concept_id).filter(
        patient_id__in=controlled_patient_id_set).exclude(id__in=pinned_instance_id_set).all()

    for problem in problems:
        pin = MedicationPinToProblem(author=actor.profile, medication=medication, problem=problem)
        pin.save()

    pass
