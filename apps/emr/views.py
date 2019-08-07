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
import datetime
import os
from audioop import reverse

from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.models import User
from django.core.checks import messages
from django.views.generic import View
from django.views.static import serve
from ranged_response import RangedFileResponse

import project.settings as settings
from common.views import *
from emr.mysnomedct import VWProblemsSerializers
from models import UserProfile, Problem, \
    Goal, ToDo, Guideline, TextNote, PatientImage, \
    Sharing, Viewer, \
    ViewStatus, ProblemRelationship, VWProblems


@user_passes_test(lambda u: u.is_superuser)
def update(request):
    os.system('sh /home/tim/core/update.sh &')
    html = """
    <script src="//code.jquery.com/jquery-1.11.0.min.js"></script>
    <title>Update</title>
    <script>
    var seconds = 60;
    setInterval(function(){ $('#time_left').text(seconds);seconds -= 1;},1000);
    setTimeout(function() { window.location = "/" }, 60000);
    </script> Going to homepage in <span id="time_left">60</span> seconds
    """
    return HttpResponse(html)


# OLD
@login_required
def list_of_unregistered_users(request):
    users = []
    for user in User.objects.all():
        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            users.append(
                {'id': user.id,
                 'username': user.username,
                 'full_name': user.get_full_name()})
    return HttpResponse(json.dumps(users), content_type="application/json")


# OLD
@login_required
def register_users(request):
    for i in request.POST:
        try:
            user_profile = UserProfile(
                user=User.objects.get(
                    id=i.split('_')[1]), role=request.POST[i])
            user_profile.save()
            if (request.POST[i] == 'admin'):
                user = User.objects.get(id=i.split('_')[1])
                user.is_superuser = True
                user.is_staff = True
                user.save()
        except:
            pass
    return HttpResponse('saved')


def is_patient(user):
    try:
        profile = UserProfile.objects.get(user=user)
        return profile.role == 'patient'
    except:
        return False


@login_required
def list_users(request):
    users = [{'is_patient': is_patient(user), 'username': user.username, 'firstname': user.first_name,
              'lastname': user.last_name, 'id': user.id, 'sex': UserProfile.objects.get(user=user).sex,
              'contact_number': UserProfile.objects.get(user=user).phone_number,
              'birthday': UserProfile.objects.get(user=user).date_of_birth.strftime(
                  '%m/%d/%Y') if UserProfile.objects.get(user=user).date_of_birth else ''} for user in
             User.objects.all().order_by('first_name') if UserProfile.objects.filter(user=user)]
    return HttpResponse(json.dumps(users), content_type="application/json")


@login_required
def get_patient_data(request, patient_id):
    from pymedtermino import snomedct

    # Find out if user requesting the data is admin, physician, or patient
    role_of_user_requesting_the_data = UserProfile.objects.get(user=request.user).role
    # Get patient object from patient id
    patient = User.objects.get(id=patient_id)
    # We provide the problems, goals, notes, todos
    # and concept ids of the problems as well as the snomed parents and children of those problems mapped to a problem id
    # This way we can prevent duplicate problems from being added
    viewers = []

    time_threshold = datetime.datetime.now() - datetime.timedelta(seconds=5)
    viewers = list(
        set([viewer.viewer for viewer in Viewer.objects.filter(patient=patient, datetime__gte=time_threshold)]))
    raw_viewers = []
    # print 'viewers: ' + str(viewers)
    for viewer in viewers:
        # print 'viewer: ' + str(viewer)
        raw_viewers.append({'user_id': viewer.id, 'full_name': viewer.get_full_name()})
    viewers = raw_viewers
    view_status = {}
    vs = ViewStatus.objects.filter(patient=patient)
    if vs:
        if not viewers:
            vs[0].delete()
        else:
            try:
                view_status = json.loads(vs[0].status)
            except:
                pass
    # this tracking section lets us coordinate multiple people/browser windows/tabs accessing a patient page at the same time
    if 'tracking_id' in request.GET:
        tracking_id = request.GET['tracking_id']
        patient = User.objects.get(id=patient_id)

        p, created = Viewer.objects.get_or_create(patient=patient, viewer=request.user, tracking_id=tracking_id)
        p.save()
    if 'new_status' in request.GET:
        patient = User.objects.get(id=patient_id)
        p, created = ViewStatus.objects.get_or_create(patient=patient)
        p.status = request.GET['new_status']
        p.save()

    # allowed viewers are the patient, admin/physician, and other patients the patient has shared to
    if (not ((request.user == patient) or (role_of_user_requesting_the_data in ['admin', 'physician']) or (
            Sharing.objects.filter(patient=patient, other_patient=request.user)))):
        return HttpResponse("Not allowed")
    # Right now only users with role == patient have a patient page
    if (not is_patient(patient)):
        return HttpResponse("Error: this user isn't a patient")

    data = {'problems': {'is_active': [], 'not_active': []}, 'goals': {'not_accomplished': [], 'accomplished': []},
            'notes': [], 'todos': {'not_accomplished': [], 'accomplished': []}, 'concept_ids': {}, 'viewers': viewers,
            'view_status': view_status}
    if 'get_only_status' in request.GET:
        return HttpResponse(json.dumps(data), content_type="application/json")
        # At this point we know the user is allowed to view this patient.
        # Now we have to detrimine what data can be provided to the requesting user
        # If the user requesting the patient data is the targeted patient or an admin or physician then we know it's OK to provide all the data
        # if ((request.user == patient) or (role_of_user_requesting_the_data in ['admin', 'physician'])):
        # Get all problems for the patient 
        # problems_query = Problem.objects.filter(patient=patient).order_by('problem_name').order_by('-authenticated')
        # Otherwise the requesting user is only allowed to see some of the patient's info
        # else:
        # Get just the problems shared to the user
    #    problems_query = [i.item for i in Sharing.objects.filter(content_type=ContentType.objects.get(app_label="emr", model="problem"), patient=patient, other_patient=request.user)]
    problems_query = Problem.objects.filter(patient=patient).order_by('problem_name').order_by('-authenticated')

    for problem in problems_query.filter(is_active=True):
        # We store the data for this problem in a dictionary called "d"
        d = {}
        d['problem_id'] = problem.id
        d['start_date'] = problem.start_date.strftime('%m/%d/%Y')
        effected_by = {}
        for i in problems_query.filter(is_active=True):
            if i == problem:
                continue
            elif ProblemRelationship.objects.filter(source=i, target=problem):
                effected_by[int(i.id)] = True
            else:
                effected_by[int(i.id)] = False
        d['effected_by'] = effected_by
        affects = {}
        for i in problems_query.filter(is_active=True):
            if i == problem:
                continue
            elif ProblemRelationship.objects.filter(source=problem, target=i):
                affects[int(i.id)] = True
            else:
                affects[int(i.id)] = False
        d['affects'] = affects
        d['problem_name'] = problem.problem_name
        d['images'] = [g.image.url for g in PatientImage.objects.filter(problem=problem)]
        d['guidelines'] = [{'guideline': g.guideline, 'reference_url': g.reference_url, 'form': g.get_form()} for g in
                           Guideline.objects.filter(concept_id=problem.concept_id)]
        d['is_controlled'] = problem.is_controlled
        d['is_authenticated'] = problem.authenticated
        d['is_active'] = problem.is_active
        d['goals'] = [{'id': g.id, 'start_date': g.start_date.strftime('%m/%d/%Y'), 'goal': g.goal,
                       'is_controlled': g.is_controlled, 'accomplished': g.accomplished,
                       'notes': [{'note': n.note} for n in g.notes.all().order_by('-datetime')]} for g in
                      Goal.objects.filter(problem=problem, accomplished=False)]
        d['todos'] = [{'todo': g.todo, 'id': g.id, 'accomplished': g.accomplished} for g in
                      ToDo.objects.filter(problem=problem, accomplished=False)]
        d['notes'] = {'by_physician': [{'note': g.note} for g in
                                       TextNote.objects.filter(problem=problem, by__in=['physician', 'admin']).order_by(
                                           '-datetime')], 'by_patient': [{'note': g.note} for g in
                                                                         TextNote.objects.filter(problem=problem,
                                                                                                 by='patient').order_by(
                                                                             '-datetime')],
                      'all': [{'by': g.by, 'note': g.note} for g in TextNote.objects.filter(problem=problem)]}
        data['problems']['is_active'].append(d)
        try:
            data['concept_ids'][problem.concept_id] = problem.id

            for j in [i.__dict__ for i in snomedct.SNOMEDCT[int(problem.concept_id)].parents]:
                data['concept_ids'][j['code']] = problem.id
            for j in [i.__dict__ for i in snomedct.SNOMEDCT[int(problem.concept_id)].children]:
                data['concept_ids'][j['code']] = problem.id
        except:
            pass
    for problem in problems_query.filter(is_active=False):
        # We store the data for this problem in a dictionary called "d"
        d = {}
        d['problem_id'] = problem.id
        d['start_date'] = problem.start_date.strftime('%m/%d/%Y')
        d['effected_by'] = problem.parent.id if problem.parent else None
        d['affects'] = [{'problem_id': g.id, 'problem_name': g.problem_name} for g in problem.get_children()]
        d['problem_name'] = problem.problem_name
        d['images'] = [g.image.url for g in PatientImage.objects.filter(problem=problem)]
        d['guidelines'] = [{'guideline': g.guideline, 'reference_url': g.reference_url} for g in
                           Guideline.objects.filter(concept_id=problem.concept_id)]
        d['is_controlled'] = problem.is_controlled
        d['is_authenticated'] = problem.authenticated
        d['is_active'] = problem.is_active
        d['goals'] = [{'id': g.id, 'start_date': g.start_date.strftime('%m/%d/%Y'), 'goal': g.goal,
                       'is_controlled': g.is_controlled, 'accomplished': g.accomplished,
                       'notes': [{'note': n.note} for n in g.notes.all().order_by('-datetime')]} for g in
                      Goal.objects.filter(problem=problem, accomplished=False)]
        d['todos'] = [{'todo': g.todo, 'id': g.id, 'accomplished': g.accomplished} for g in
                      ToDo.objects.filter(problem=problem, accomplished=False)]
        d['notes'] = {'by_physician': [{'note': g.note} for g in
                                       TextNote.objects.filter(problem=problem, by__in=['physician', 'admin']).order_by(
                                           '-datetime')], 'by_patient': [{'note': g.note} for g in
                                                                         TextNote.objects.filter(problem=problem,
                                                                                                 by='patient').order_by(
                                                                             '-datetime')],
                      'all': [{'by': g.by, 'note': g.note} for g in TextNote.objects.filter(problem=problem)]}
        data['problems']['not_active'].append(d)
        try:
            data['concept_ids'][problem.concept_id] = problem.id

            for j in [i.__dict__ for i in snomedct.SNOMEDCT[int(problem.concept_id)].parents]:
                data['concept_ids'][j['code']] = problem.id
            for j in [i.__dict__ for i in snomedct.SNOMEDCT[int(problem.concept_id)].children]:
                data['concept_ids'][j['code']] = problem.id
        except:
            pass
    for goal in Goal.objects.filter(patient=patient, accomplished=False).order_by('goal'):
        d = {}
        d['for_problem'] = goal.problem.problem_name if goal.problem else ''
        d['goal_id'] = goal.id
        d['goal'] = goal.goal
        d['start_date'] = goal.start_date.strftime('%m/%d/%y')
        d['is_controlled'] = goal.is_controlled
        d['accomplished'] = goal.accomplished
        d['notes'] = [{'note': n.note} for n in goal.notes.all().order_by('-datetime')]
        data['goals']['not_accomplished'].append(d)
    for todo in ToDo.objects.filter(patient=patient, accomplished=False).order_by('todo'):
        d = {}
        d['for_problem'] = todo.problem.problem_name if todo.problem else ''
        d['todo_id'] = todo.id
        d['todo'] = todo.todo
        d['accomplished'] = todo.accomplished
        data['todos']['not_accomplished'].append(d)
    for todo in ToDo.objects.filter(patient=patient, accomplished=True).order_by('todo'):
        d = {}
        d['for_problem'] = todo.problem.problem_name if todo.problem else ''
        d['todo_id'] = todo.id
        d['todo'] = todo.todo
        d['accomplished'] = todo.accomplished
        data['todos']['accomplished'].append(d)

    return HttpResponse(json.dumps(data), content_type="application/json")


@login_required
def change_status(request):
    role = UserProfile.objects.get(user=request.user).role

    authenticated = True if (role == 'physician' or role == 'admin') else False
    # print request.POST
    if request.POST['target'] == 'problem':
        problem = Problem.objects.get(id=request.POST['id'])
        problem.authenticated = authenticated
        value = True if request.POST['value'] == 'true' else False
        if (request.POST['attr'] == 'authenticated' and role == 'patient'):
            return HttpResponse("patients can't authenticate problems")

        setattr(problem, request.POST['attr'], value)
        problem.save()
    elif request.POST['target'] == 'goal':
        goal = Goal.objects.get(id=request.POST['id'])
        if goal.problem:
            goal.problem.authenticated = authenticated
            goal.problem.save()
        value = True if request.POST['value'] == 'true' else False
        setattr(goal, 'accomplished', value)
        goal.save()
    elif request.POST['target'] == 'goal_is_controlled':
        goal = Goal.objects.get(id=request.POST['id'])
        if goal.problem:
            goal.problem.authenticated = authenticated
            goal.problem.save()
        value = True if request.POST['value'] == 'true' else False
        setattr(goal, 'is_controlled', value)
        goal.save()
    elif request.POST['target'] == 'todo':
        todo = ToDo.objects.get(id=request.POST['id'])
        if todo.problem:
            todo.problem.authenticated = authenticated
            todo.problem.save()
        value = True if request.POST['value'] == 'true' else False
        setattr(todo, 'accomplished', value)
        todo.save()
    elif request.POST['attr'] == 'effected_by':
        problem = Problem.objects.get(id=request.POST['id'])
        problem.authenticated = authenticated
        problem.save()
        if request.POST['value'] == 'true':
            pr = ProblemRelationship(source=Problem.objects.get(id=request.POST['target']),
                                     target=Problem.objects.get(id=request.POST['id']))
            pr.save()
        else:
            pr = ProblemRelationship.objects.get(source=Problem.objects.get(id=request.POST['target']),
                                                 target=Problem.objects.get(id=request.POST['id']))
            pr.delete()
    elif request.POST['attr'] == 'affects':
        problem = Problem.objects.get(id=request.POST['id'])
        problem.authenticated = authenticated
        problem.save()
        if request.POST['value'] == 'true':
            pr = ProblemRelationship(source=Problem.objects.get(id=request.POST['id']),
                                     target=Problem.objects.get(id=request.POST['target']))
            pr.save()
        else:
            pr = ProblemRelationship.objects.get(source=Problem.objects.get(id=request.POST['id']),
                                                 target=Problem.objects.get(id=request.POST['target']))
            pr.delete()
    return HttpResponse('saved')


@login_required
def add_problem(request, patient_id):
    role = UserProfile.objects.get(user=request.user).role
    authenticated = True if (role == 'physician' or role == 'admin') else False
    if 'problem_name' in request.POST:
        problem = Problem(patient=User.objects.get(id=patient_id), problem_name=request.POST['problem_name'],
                          concept_id=request.POST['concept_id'], authenticated=authenticated)
        problem.save()
    elif 'goal' in request.POST:
        goal = Goal(patient=User.objects.get(id=patient_id), goal=request.POST['goal'])
        goal.save()
    elif 'todo' in request.POST:
        # print 'todo'
        # print request.POST
        todo = ToDo(patient=User.objects.get(id=patient_id), todo=request.POST['todo'])
        todo.save()
    return HttpResponse('added')


def save_patient_summary(request, patient_id):
    profile = UserProfile.objects.get(user=User.objects.get(id=patient_id))
    profile.summary = request.POST['summary']
    profile.save()
    return HttpResponseRedirect('/patient/%s/' % (patient_id))


class AuthComplete(View):
    def get(self, request, *args, **kwargs):
        backend = kwargs.pop('backend')
        try:
            return complete(request, backend, *args, **kwargs)
        except AuthFailed:
            messages.error(
                request,
                "Your Google Apps domain isn't authorized for this app")
            return HttpResponseRedirect(reverse('home'))


class LoginError(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse(status=401)


# ****************** New Code *********************
@login_required
def list_snomed_terms(request):
    query = request.GET['query']
    result = VWProblems.objects.using('snomedict').filter(term__contains="{0}".format(query)).all()
    results_holder = VWProblemsSerializers(result, many=True).data
    return ajax_response(results_holder)


def has_read_permission(request, path):
    """ Only show to authenticated users"""
    # Note this could allow access to paths including ../..
    # Don't use this simple check in production!
    return request.user.is_authenticated()


def serve_private_file(request, path):
    """
    Simple example of a view to serve private files with xsendfile"
    :param request:
    :param path:
    :return:
    """
    if has_read_permission(request, path):
        fileRes = serve(request, path, settings.MEDIA_ROOT, False)
        response = RangedFileResponse(request, fileRes.file_to_stream, fileRes._headers['content-type'][1])
        return response
    else:
        return HttpResponseForbidden()
