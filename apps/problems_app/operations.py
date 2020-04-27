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
from emr.models import ProblemActivity, SharingPatient, AOneC, ColonCancerScreening


@timeit
def add_problem_activity(problem, user, activity, put_type=None):
    new_activity = ProblemActivity(problem=problem, author=user, activity=activity)
    if put_type == 'input':
        new_activity.is_input_type = True
    if put_type == 'output':
        new_activity.is_output_type = True
    new_activity.save()


@timeit
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


@timeit
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
