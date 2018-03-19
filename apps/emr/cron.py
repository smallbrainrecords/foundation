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
import datetime

import cronjobs
from django.contrib.auth.models import User
from django.db.models import Max, Count

from common.views import timeit
from emr.models import ColonCancerScreening, Problem, ToDo, Label, \
    PatientController, TaggedToDoOrder, AOneC, ObservationPinToProblem, Observation, MedicationPinToProblem, \
    Medication, ProblemRelationship
from emr.operations import op_add_event
from problems_app.operations import add_problem_activity


def age(when, on=None):
    if on is None:
        on = datetime.date.today()
    was_earlier = (on.month, on.day) < (when.month, when.day)
    return on.year - when.year - was_earlier


@cronjobs.register
def review_colorectal_cancer_risk_assessment():

    print('Starting cron review_colorectal_cancer_risk_assessment...')

    colon_cancers = ColonCancerScreening.objects.all()
    for colon_cancer in colon_cancers:
        if not colon_cancer.todo_past_five_years and age(colon_cancer.patient.profile.date_of_birth) >= 20 and \
                (colon_cancer.colon_risk_factors.count() == 0 or age(colon_cancer.last_risk_updated_date) >= 5):
            todo = 'review colorectal cancer risk assessment'
            new_todo = ToDo(patient=colon_cancer.patient, problem=colon_cancer.problem, todo=todo)

            order = ToDo.objects.all().aggregate(Max('order'))
            if not order['order__max']:
                order = 1
            else:
                order = order['order__max'] + 1
            new_todo.order = order
            new_todo.save()

            if not Label.objects.filter(name="screening", css_class="todo-label-yellow", is_all=True).exists():
                label = Label(name="screening", css_class="todo-label-yellow", is_all=True)
                label.save()
            else:
                label = Label.objects.get(name="screening", css_class="todo-label-yellow", is_all=True)
            new_todo.colon_cancer = colon_cancer
            new_todo.save()
            new_todo.labels.add(label)

            colon_cancer.todo_past_five_years = True
            colon_cancer.save()
    print('Finished cron review_colorectal_cancer_risk_assessment...')
    print('')


@cronjobs.register
def patient_needs_a_plan_for_colorectal_cancer_screening():

    print('Starting cron patient_needs_a_plan_for_colorectal_cancer_screening...')

    colon_cancers = ColonCancerScreening.objects.all()
    for colon_cancer in colon_cancers:
        if colon_cancer.colon_cancer_todos.count() == 0 and age(colon_cancer.patient.profile.date_of_birth) >= 50:
            todo = 'patient needs a plan for colorectal cancer screening'
            due_date = datetime.date(colon_cancer.patient.profile.date_of_birth.year + 50,
                                     colon_cancer.patient.profile.date_of_birth.month,
                                     colon_cancer.patient.profile.date_of_birth.day)
            new_todo = ToDo(patient=colon_cancer.patient, problem=colon_cancer.problem, todo=todo, due_date=due_date)

            order = ToDo.objects.all().aggregate(Max('order'))
            if not order['order__max']:
                order = 1
            else:
                order = order['order__max'] + 1
            new_todo.order = order
            new_todo.save()

            if not Label.objects.filter(name="screening", css_class="todo-label-yellow", is_all=True).exists():
                label = Label(name="screening", css_class="todo-label-yellow", is_all=True)
                label.save()
            else:
                label = Label.objects.get(name="screening", css_class="todo-label-yellow", is_all=True)
            new_todo.colon_cancer = colon_cancer
            new_todo.save()
            new_todo.labels.add(label)

            controllers = PatientController.objects.filter(patient=colon_cancer.patient)
            for controller in controllers:
                new_todo.members.add(controller.physician)
                TaggedToDoOrder.objects.create(todo=new_todo, user=controller.physician)

    print('Finished cron patient_needs_a_plan_for_colorectal_cancer_screening...')
    print('')


@cronjobs.register
def a1c_order_was_automatically_generated():

    print('Starting cron a1c_order_was_automatically_generated...')

    a1cs = AOneC.objects.all()
    for a1c in a1cs:
        if a1c.observation.observation_components.all():
            first_component = a1c.observation.observation_components.all().first()
            if first_component.observation_component_values.count() and a1c.todo_past_six_months == False:
                last_measurement = first_component.observation_component_values.all().last()
                date = last_measurement.created_on.day
                month = last_measurement.created_on.month + 6
                year = last_measurement.created_on.year
                if month > 12:
                    month = month - 12
                    year = year + 1

                due_date = datetime.date(year, month, date)
                if datetime.date.today() >= due_date:
                    todo = 'A1C order was automatically generated'
                    new_todo = ToDo(patient=a1c.problem.patient, problem=a1c.problem, todo=todo, due_date=due_date)

                    order = ToDo.objects.all().aggregate(Max('order'))
                    if not order['order__max']:
                        order = 1
                    else:
                        order = order['order__max'] + 1
                    new_todo.order = order
                    new_todo.a1c = a1c
                    new_todo.save()

                    a1c.todo_past_six_months = True
                    a1c.save()

    print('Finished cron a1c_order_was_automatically_generated...')
    print('')


@timeit
@cronjobs.register
def physician_adds_the_same_data_to_the_same_problem_concept_id_more_than_3_times():
    """
    Refer: https://trello.com/c/DSAQoLCw -> https://trello.com/c/UDwAXH4H
    Critical issues:
    - [DONE] Observation's LOINC code is always null -> Resolution: Update LOINC code for all Observation record
    - [DONE] While adding default data for patient save LOINC code also
    - [DONE] While adding custom data save LOINC code in observation & it's component also
    # STEP 2: Find all PATIENT having both data LOINC code and problem CONCEPT_ID
    # STEP 3: If they are note pinned then do the work
    :return:
    """
    print('Starting cron physician_adds_the_same_data_to_the_same_problem_concept_id_more_than_3_times...')

    # Default actor for cron job
    actor = User.objects.filter(profile__role='admin').first()

    # then that data is added to all patients for that problem
    pins = ObservationPinToProblem.objects.filter(author__profile__role="physician").filter(
        problem__concept_id__isnull=False, observation__code__isnull=False).values('problem__concept_id',
                                                                                   'observation__code').annotate(
        total=Count('problem__concept_id')).filter(total__gte=3)
    print("Existing pins count: {}".format(pins.query))
    print('')

    for pin in pins:
        print("Processing pin pair: Observation: {} - Problem:{}".format(pin['observation__code'],
                                                                         pin['problem__concept_id']))
        print('')
        for p in User.objects.filter(profile__role='patient').all():
            patient_observation = Observation.objects.filter(subject_id=p.id, code=pin['observation__code'])
            patient_problem = Problem.objects.filter(patient_id=p.id, concept_id=pin['problem__concept_id'])
            print("Processing patient:({}) {}".format(p.id, p))
            print("Observation: {} ".format(patient_observation.exists()))
            print("Problem: {} ".format(patient_problem.exists()))
            print('')
            if patient_observation.exists() and patient_problem.exists():
                if not ObservationPinToProblem.objects.filter(problem=patient_problem.get(),
                                                              observation=patient_observation.get()).exists():
                    p = ObservationPinToProblem(problem=patient_problem.get(), author=actor,
                                                observation=patient_observation.get())
                    p.save()

    print('Finished cron physician_adds_the_same_data_to_the_same_problem_concept_id_more_than_3_times...')
    print('')


@cronjobs.register
def physician_adds_the_same_medication_to_the_same_problem_concept_id_more_than_3_times():
    # then that medication is added to all patients for that problem

    print('Starting cron physician_adds_the_same_medication_to_the_same_problem_concept_id_more_than_3_times...')

    pins = MedicationPinToProblem.objects.filter(author__profile__role="physician")
    for pin in pins:
        if pin.medication.concept_id and pin.problem.concept_id:
            if MedicationPinToProblem.objects.filter(author__profile__role="physician",
                                                     medication__concept_id=pin.medication.concept_id,
                                                     problem__concept_id=pin.problem.concept_id).count() > 3:
                problems = Problem.objects.filter(concept_id=pin.problem.concept_id)
                for problem in problems:
                    if Medication.objects.filter(concept_id=pin.medication.concept_id,
                                                 inr__patient=problem.patient).exists():
                        medications = Medication.objects.filter(concept_id=pin.medication.concept_id,
                                                                inr__patient=problem.patient)
                        for medication in medications:
                            if not MedicationPinToProblem.objects.filter(problem=problem,
                                                                         medication=medication).exists():
                                p = MedicationPinToProblem(problem=problem, author=pin.author, medication=medication)
                                p.save()

    print('Finished cron physician_adds_the_same_medication_to_the_same_problem_concept_id_more_than_3_times...')
    print('')


@cronjobs.register
def problem_relationship_auto_pinning_for_3_times_matched():
    """
    https://trello.com/c/TWI2l0UU
    If any two SNOMED CT CONCEPT_IDs are set as relationship more than 3 times
    then set this as a relationship for all patients who have those two problems.
    :return:
    """
    print('Starting cron problem_relationship_auto_pinning_for_3_times_matched...')
    # Default actor for cron job
    actor = User.objects.filter(profile__role='admin').first()

    # Find all paired problem have same SNOMED CT id
    relationships = ProblemRelationship.objects.filter(source__concept_id__isnull=False,
                                                       target__concept_id__isnull=False) \
        .values('source__concept_id', 'target__concept_id').annotate(total=Count('source__concept_id')).filter(
        total__gte=3)

    # find_all_problem_relationship_more_than_3_time()
    print('Find all paired problem have same SNOMED CT...')
    print(relationships)
    print('')

    for relation in relationships:
        print("Processing problem relationship source: {}- target {}".format(relation['source__concept_id'],
                                                                             relation['target__concept_id']))
        for p in User.objects.filter(profile__role='patient').all():
                problem_pairs = Problem.objects.filter(patient_id=p.id).filter(
                    concept_id__in=[relation['source__concept_id'], relation['target__concept_id']])
                print("Processing patient:({}) {}".format(p.id, p))
                print("Number of problems in pair: {}".format(problem_pairs.count()))
                if problem_pairs.exists() and problem_pairs.count() == 2:
                    source = Problem.objects.get(patient_id=p.id, concept_id=relation['source__concept_id'])
                    target = Problem.objects.get(patient_id=p.id, concept_id=relation['target__concept_id'])

                    if not ProblemRelationship.objects.filter(source=source, target=target).exists():
                        ProblemRelationship.objects.create(source=source, target=target)
                        activity = "Created Problem Relationship(automation pinning): <b>{0}</b> effects <b>{1}</b>".format(
                            source.problem_name, target.problem_name)
                        # Add log
                        add_problem_activity(source, actor, activity)
                        add_problem_activity(target, actor, activity)
                        op_add_event(actor, source.patient, activity)
                        print("Activity log: {}".format(activity))
                print('')
    print('Finished cron problem_relationship_auto_pinning_for_3_times_matched...')
    print('')
