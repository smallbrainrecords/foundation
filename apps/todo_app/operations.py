
from emr.models import TodoActivity


def add_todo_activity(todo, user_profile, activity, comment=None, attachment=None):
	new_activity = TodoActivity(
		todo=todo, author=user_profile, activity=activity)
	if comment:
		new_activity.comment = comment
	if attachment:
		new_activity.attachment = attachment
	new_activity.save()
