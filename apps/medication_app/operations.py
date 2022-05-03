"""
Copyright (c) Small Brain Records 2014-2018 Kevin Perdue, James Ryan with contributors Timothy Clemens and Dinh Ngoc Anh

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""
from common.views import timeit
from emr.models import Encounter, EncounterEvent, ProblemActivity, MedicationPinToProblem, PatientController, Problem, \
    EncounterMedication


@timeit
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
    latest_encounter = Encounter.objects.filter(
        physician=actor, patient=patient).order_by('-id')

    if latest_encounter.exists():
        latest_encounter = latest_encounter[0]

        if latest_encounter.is_active():
            encounter_event = EncounterEvent(
                encounter=latest_encounter, summary=summary)
            encounter_event.save()

    # Add log to pinned problem activity
    problems = medication.problem_set.all()
    for problem in problems:
        activity = ProblemActivity(
            problem=problem, author=actor, activity=summary)
        activity.save()

    pass


@timeit
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
        pinned_instance = MedicationPinToProblem.objects.filter(author=actor).filter(
            medication__concept_id=medication.concept_id).filter(
            problem__concept_id=problem.concept_id)
        return pinned_instance, pinned_instance.count()
    pass


@timeit
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
    controlled_patient_id_set = [int(x.patient.id)
                                 for x in controlled_patients]
    pinned_instance_id_set = [int(x.problem_id) for x in pinned_instance_set]

    # Filtered out all problem already pinned to this medication
    problems = Problem.objects.filter(concept_id=problem.concept_id).filter(
        patient_id__in=controlled_patient_id_set).exclude(id__in=pinned_instance_id_set).all()

    for problem in problems:
        pin = MedicationPinToProblem(
            author=actor, medication=medication, problem=problem)
        pin.save()

    pass


@timeit
def op_track_medication_during_encounter(patient_id, medication_id):
    """
    TODO: This can make to a separated encounter medication app
    :param patient_id:
    :param medication_id:
    :return:
    """
    encounters = Encounter.objects.filter(
        patient_id=patient_id).order_by('-id')
    if encounters.exists():
        encounter = encounters[0]

        if encounter.is_active() and not EncounterMedication.objects.filter(encounter=encounter,
                                                                            medication_id=medication_id).exists():
            medication_encounter = EncounterMedication(
                encounter=encounter, medication_id=medication_id)
            medication_encounter.save()
    pass
