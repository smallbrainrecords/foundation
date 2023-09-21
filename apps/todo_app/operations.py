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
from emr.models import TodoActivity, UserProfile


#@timeit
def add_todo_activity(todo, user, activity, comment=None, attachment=None):
    new_activity = TodoActivity(todo=todo, author=user, activity=activity)
    if comment:
        new_activity.comment = comment
    if attachment:
        new_activity.attachment = attachment
    new_activity.save()


#@timeit
def is_patient(user):
    try:
        profile = UserProfile.objects.get(user=user)
        return profile.role == 'patient'
    except UserProfile.DoesNotExist:
        return False


# set problem authentication to false if not physician, admin
#@timeit
def set_problem_authentication_false(request, todo):
    if todo.problem:
        problem = todo.problem
        actor_profile = UserProfile.objects.get(user=request.user)
        authenticated = actor_profile.role in ("physician", "admin")
        problem.authenticated = authenticated
        problem.save()
