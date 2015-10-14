
from emr.models import ProblemActivity


def add_problem_activity(problem, user_profile, activity):
    new_activity = ProblemActivity(
        problem=problem, author=user_profile, activity=activity)
    new_activity.save()
