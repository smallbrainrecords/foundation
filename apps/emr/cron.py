import datetime

import cronjobs
from django.db.models import Max

from emr.models import ColonCancerScreening, Problem, ToDo, Label, \
	PatientController, TaggedToDoOrder, AOneC, ObservationPinToProblem, Observation, MedicationPinToProblem, \
	Medication


def age(when, on=None):
    if on is None:
        on = datetime.date.today()
    was_earlier = (on.month, on.day) < (when.month, when.day)
    return on.year - when.year - (was_earlier)


@cronjobs.register
def review_colorectal_cancer_risk_assessment():
	colon_cancers = ColonCancerScreening.objects.all()
	for colon_cancer in colon_cancers:
		if not colon_cancer.todo_past_five_years and age(colon_cancer.patient.profile.date_of_birth) >= 20 and \
		(colon_cancer.colon_risk_factors.count() == 0 or age(colon_cancer.last_risk_updated_date) >= 5):
			todo = 'review colorectal cancer risk assessment'
			new_todo = ToDo(patient=colon_cancer.patient, problem=colon_cancer.problem, todo=todo)

			order =  ToDo.objects.all().aggregate(Max('order'))
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


@cronjobs.register
def patient_needs_a_plan_for_colorectal_cancer_screening():
	colon_cancers = ColonCancerScreening.objects.all()
	for colon_cancer in colon_cancers:
		if colon_cancer.colon_cancer_todos.count() == 0 and age(colon_cancer.patient.profile.date_of_birth) >= 50:
			todo = 'patient needs a plan for colorectal cancer screening'
			due_date = datetime.date(colon_cancer.patient.profile.date_of_birth.year + 50,
									 colon_cancer.patient.profile.date_of_birth.month,
									 colon_cancer.patient.profile.date_of_birth.day)
			new_todo = ToDo(patient=colon_cancer.patient, problem=colon_cancer.problem, todo=todo, due_date=due_date)

			order =  ToDo.objects.all().aggregate(Max('order'))
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

@cronjobs.register
def a1c_order_was_automatically_generated():
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

					order =  ToDo.objects.all().aggregate(Max('order'))
					if not order['order__max']:
						order = 1
					else:
						order = order['order__max'] + 1
					new_todo.order = order
					new_todo.a1c = a1c
					new_todo.save()

					a1c.todo_past_six_months = True
					a1c.save()

@cronjobs.register
def physician_adds_the_same_data_to_the_same_problem_concept_id_more_than_3_times():
	# then that data is added to all patients for that problem
	pins = ObservationPinToProblem.objects.filter(author__profile__role="physician")
	for pin in pins:
		if pin.observation.code and pin.problem.concept_id:
			if ObservationPinToProblem.objects.filter(author__profile__role="physician", observation__code=pin.observation.code, problem__concept_id=pin.problem.concept_id).count() > 3:
				problems = Problem.objects.filter(concept_id=pin.problem.concept_id)
				for problem in problems:
					if Observation.objects.filter(code=pin.observation.code, subject=problem.patient).exists():
						observations = Observation.objects.filter(code=pin.observation.code, subject=problem.patient)
						for observation in observations:
							if not ObservationPinToProblem.objects.filter(problem=problem, observation=observation).exists():
								p = ObservationPinToProblem(problem=problem, author=pin.author, observation=observation)
								p.save()

@cronjobs.register
def physician_adds_the_same_medication_to_the_same_problem_concept_id_more_than_3_times():
	# then that medication is added to all patients for that problem
	pins = MedicationPinToProblem.objects.filter(author__role="physician")
	for pin in pins:
		if pin.medication.concept_id and pin.problem.concept_id:
			if MedicationPinToProblem.objects.filter(author__role="physician", medication__concept_id=pin.medication.concept_id, problem__concept_id=pin.problem.concept_id).count() > 3:
				problems = Problem.objects.filter(concept_id=pin.problem.concept_id)
				for problem in problems:
					if Medication.objects.filter(concept_id=pin.medication.concept_id, inr__patient=problem.patient).exists():
						medications = Medication.objects.filter(concept_id=pin.medication.concept_id, inr__patient=problem.patient)
						for medication in medications:
							if not MedicationPinToProblem.objects.filter(problem=problem, medication=medication).exists():
								p = MedicationPinToProblem(problem=problem, author=pin.author, medication=medication)
								p.save()