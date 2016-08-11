import cronjobs
import datetime
from django.contrib.auth.models import User
from django.db.models import Max, Prefetch
from emr.models import ColonCancerScreening, ColonCancerStudy, RiskFactor, UserProfile, Problem, ToDo, Label

def age(when, on=None):
    if on is None:
        on = datetime.date.today()
    was_earlier = (on.month, on.day) < (when.month, when.day)
    return on.year - when.year - (was_earlier)

@cronjobs.register
def review_colorectal_cancer_risk_assessment():
	colon_cancers = ColonCancerScreening.objects.all()
	for colon_cancer in colon_cancers:
		if not colon_cancer.todo_past_five_years and age(colon_cancer.patient.date_of_birth) >=20 and \
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

			if not Label.objects.filter(author=colon_cancer.patient.user, name="screening", css_class="todo-label-yellow").exists():
				label = Label(author=colon_cancer.patient.user, name="screening", css_class="todo-label-yellow", is_all=True)
				label.save()
			else:
				label = Label.objects.get(author=colon_cancer.patient.user, name="screening", css_class="todo-label-yellow", is_all=True)
			new_todo.colon_cancer = colon_cancer
			new_todo.save()
			new_todo.labels.add(label)

			colon_cancer.todo_past_five_years = True
			colon_cancer.save()
			print new_todo
