import cronjobs
import datetime
from django.contrib.auth.models import User
from django.db.models import Max, Prefetch
from emr.models import ColonCancerScreening, ColonCancerStudy, RiskFactor, UserProfile, Problem, ToDo, Label, \
	PatientController, TaggedToDoOrder, Observation

def age(when, on=None):
    if on is None:
        on = datetime.date.today()
    was_earlier = (on.month, on.day) < (when.month, when.day)
    return on.year - when.year - (was_earlier)

@cronjobs.register
def review_colorectal_cancer_risk_assessment():
	colon_cancers = ColonCancerScreening.objects.all()
	for colon_cancer in colon_cancers:
		if not colon_cancer.todo_past_five_years and age(colon_cancer.patient.date_of_birth) >= 20 and \
		(colon_cancer.colon_risk_factors.count() == 0 or age(colon_cancer.last_risk_updated_date) >= 5):
			todo = 'review colorectal cancer risk assessment'
			new_todo = ToDo(patient=colon_cancer.patient.user, problem=colon_cancer.problem, todo=todo)

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
		if colon_cancer.colon_cancer_todos.count() == 0 and age(colon_cancer.patient.date_of_birth) >= 50:
			todo = 'patient needs a plan for colorectal cancer screening'
			due_date = datetime.date(colon_cancer.patient.date_of_birth.year + 50, colon_cancer.patient.date_of_birth.month, colon_cancer.patient.date_of_birth.day)
			new_todo = ToDo(patient=colon_cancer.patient.user, problem=colon_cancer.problem, todo=todo, due_date=due_date)

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

			controllers = PatientController.objects.filter(patient=colon_cancer.patient.user)
			for controller in controllers:
				new_todo.members.add(controller.physician.profile)
				tagged_todo = TaggedToDoOrder.objects.create(todo=new_todo, user=controller.physician)

@cronjobs.register
def observation_order_was_automatically_generated():
	observations = Observation.objects.all()
	for observation in observations:
		if observation.observation_components.count() and observation.todo_past_six_months == False:
			last_measurement = observation.observation_components.all().last()
			date = last_measurement.created_on.day
			month = last_measurement.created_on.month + 6
			year = last_measurement.created_on.year
			if month > 12:
				month = month - 12
				year = year + 1

			due_date = datetime.date(year, month, date)
			if datetime.date.today() >= due_date:
				todo = 'A1C order was automatically generated'
				new_todo = ToDo(patient=observation.problem.patient, problem=observation.problem, todo=todo, due_date=due_date)

				order =  ToDo.objects.all().aggregate(Max('order'))
				if not order['order__max']:
					order = 1
				else:
					order = order['order__max'] + 1
				new_todo.order = order
				new_todo.observation = observation
				new_todo.save()

				observation.todo_past_six_months = True
				observation.save()
