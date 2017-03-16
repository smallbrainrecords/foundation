from emr.models import ProblemActivity, SharingPatient, AOneC, ColonCancerScreening


def add_problem_activity(problem, user_profile, activity, put_type=None):
    new_activity = ProblemActivity(problem=problem, author=user_profile, activity=activity)
    if put_type == 'input':
        new_activity.is_input_type = True
    if put_type == 'output':
        new_activity.is_output_type = True
    new_activity.save()


def check_problem_access(user, problem):
    """

    :param user:
    :param problem:
    :return:
    """
    if user.profile.role == 'patient' and user != problem.patient:
        return SharingPatient.objects.filter(sharing=user, problems__in=[problem.id]).exists()
    else:
        return True


def get_available_widget(problem_info):
    """

    :param problem_info:
    :return:
    """
    available_widgets = []

    if problem_info.concept_id in ['73211009', '46635009', '44054006']:
        AOneC.objects.create_if_not_exist(problem_info)
        available_widgets.append('a1c')

    # Add colon cancer widget to problems that have concept id 102499006
    if problem_info.concept_id in ['102499006']:
        ColonCancerScreening.objects.create_if_not_exist(problem_info)
        available_widgets.append('colon_cancers')

    # Check inr widget is available
    if problem_info.observations.filter(observation_components__component_code="6301-6").exists():
        available_widgets.append('inr')

    return available_widgets
