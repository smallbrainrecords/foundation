from emr.models import TodoActivity, UserProfile


def add_todo_activity(todo, user_profile, activity, comment=None, attachment=None):
    new_activity = TodoActivity(
        todo=todo, author=user_profile, activity=activity)
    if comment:
        new_activity.comment = comment
    if attachment:
        new_activity.attachment = attachment
    new_activity.save()


def is_patient(user):
    try:
        profile = UserProfile.objects.get(user=user)
        return profile.role == 'patient'
    except UserProfile.DoesNotExist:
        return False


# set problem authentication to false if not physician, admin
def set_problem_authentication_false(request, todo):
    if todo.problem:
        problem = todo.problem
        actor_profile = UserProfile.objects.get(user=request.user)
        authenticated = actor_profile.role in ("physician", "admin")
        problem.authenticated = authenticated
        problem.save()
