from emr.models import ProblemActivity


def add_problem_activity(problem, user_profile, activity, put_type=None):
	new_activity = ProblemActivity(problem=problem, author=user_profile, activity=activity)
	if put_type == 'input':
		new_activity.is_input_type = True
	if put_type == 'output':
		new_activity.is_output_type = True
	new_activity.save()
