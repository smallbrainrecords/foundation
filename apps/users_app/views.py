#!/usr/bin/env python
try:
    from PIL import Image, ImageOps
except ImportError:
    import Image
    import ImageOps
import operator

from common.views import *

from emr.models import UserProfile, Problem
from emr.models import Goal, ToDo
from emr.models import Encounter, Sharing, EncounterEvent, EncounterProblemRecord

from emr.models import PhysicianTeam, PatientController, ProblemOrder, ProblemActivity
from emr.models import SharingPatient

from problems_app.serializers import ProblemSerializer
from goals_app.serializers import GoalSerializer
from .serializers import UserProfileSerializer
from todo_app.serializers import TodoSerializer
from encounters_app.serializers import EncounterSerializer, EncounterEventSerializer

from .forms import LoginForm, RegisterForm, UpdateBasicProfileForm, UpdateProfileForm, UpdateEmailForm

import datetime

from emr.manage_patient_permissions import ROLE_PERMISSIONS, check_permissions

from emr.manage_patient_permissions import check_access


def is_patient(user):
    try:
        profile = UserProfile.objects.get(user=user)
        return profile.role == 'patient'
    except UserProfile.DoesNotExist:
        return False


def login_user(request):
    if request.method == 'POST':
        logout(request)

        form = LoginForm(request.POST)

        errors = []
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(username=username, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    return HttpResponseRedirect('/u/home/')
                else:
                    errors.append('User is not verified or active.')
            else:
                errors.append('Incorrect username or password.')
        else:
            errors.append('Please fill valid data.')

        content = {'login_errors': errors, 'form': form}

        return render(
            request,
            'users/login.html',
            content)

    if request.method == 'GET':
        content = {}
        return render(
            request,
            'users/login.html',
            content)


def logout_user(request):
    logout(user)
    return HttpResponseRedirect('/u/login/')


def register_user(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)

        errors = []

        if form.is_valid():

            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            verify_password = form.cleaned_data['verify_password']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']

            user_exists = User.objects.filter(
                Q(email=email) | Q(username=email)).exists()

            if len(password) > 2 and password == verify_password:

                if not user_exists:
                    current = datetime.datetime.now()
                    user = User(
                        username=email,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        last_login=current)
                    user.set_password(password)
                    user.save()

                    user = authenticate(username=email, password=password)
                    login(request, user)

                    return HttpResponseRedirect('/u/home')

                else:
                    errors.append(
                        'User with same email or username already exists')
            else:
                errors.append('Passwords must match')
        else:
            errors.append('Please fill data')

        content = {}
        content['register_form'] = form
        content['register_errors'] = errors

        return render(
            request,
            'users/login.html',
            content)


@login_required
def home(request):

    if request.method == 'GET':

        user = request.user

        try:
            user_profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            user_profile = None

        if user_profile is not None:
            role = user_profile.role

            if role in ['admin']:
                # Manage Users
                return HttpResponseRedirect('/project/admin')
            if role == 'patient':
                # Manage Patient
                return HttpResponseRedirect('/u/patient/manage/%s/' % user.id)
            if role in ['secretary', 'nurse', 'mid-level', 'physician']:
                return HttpResponseRedirect('/u/staff/')

            return HttpResponse('Something went wrong !')

        unapproved_user_message = '''
            <script>
                setTimeout(function() { window.location = "/u/home/" }, 5000);
            </script>
            <p style="padding:100px;font-size:20px;"">
            Your account is created but your profile is not verified. <br>
            Waiting on manual approval. <br>
            <a href='/logout/'>Logout</a>
            </p>
        '''
        return HttpResponse(unapproved_user_message)


# Users
@login_required
def manage_patient(request, user_id):

    user = User.objects.get(id=user_id)
    actor_profile = UserProfile.objects.get(user=request.user)
    patient_profile = UserProfile.objects.get(user=user)

    # Allowed viewers
    # The patient, admin/physician, and other patients the patient has shared
    allowed = False
    allowed = check_access(patient_profile.user, actor_profile)

    if not allowed:
        return HttpResponse("Not allowed")
    if (not is_patient(user)):
        return HttpResponse("Error: this user isn't a patient")

    context = {}

    context['patient'] = user
    context['user_role'] = actor_profile.role
    context['patient_profile'] = patient_profile

    context = RequestContext(request, context)

    return render_to_response("manage_patient.html", context)


# Users
@login_required
def get_patient_info(request, patient_id):

    patient_user = User.objects.get(id=patient_id)
    patient_profile = UserProfile.objects.get(user=patient_user)

    # add Fit and Well: 102499006 by default
    if not Problem.objects.filter(patient=patient_user, concept_id='102499006'):
        problem = Problem()
        problem.concept_id = '102499006'
        problem.problem_name = 'Fit and well (finding)'
        problem.patient = patient_user
        problem.save()

    # Timeline Problems
    timeline_problems = Problem.objects.filter(patient=patient_user)
    timeline_problems_list = []
    for problem in timeline_problems:
        problem_dict = ProblemSerializer(problem).data
        timeline_problems_list.append(problem_dict)

    # Active Problems 
    if request.user.profile.role == 'nurse' or request.user.profile.role == 'secretary':
        team_members = PhysicianTeam.objects.filter(member=request.user)
        if team_members:
            user = team_members[0].physician
        else:
            user = request.user
    else:
        user = request.user
    try:
        problem_order = ProblemOrder.objects.get(user=user, patient=patient_user)
    except ProblemOrder.DoesNotExist:
        problem_order = ProblemOrder(user=user, patient=patient_user)
        problem_order.save()

    problem_list = []
    problems = Problem.objects.filter(patient=patient_user)
    for key in problem_order.order:
        if problems.filter(id=key):
            problem = problems.get(id=key)
            problem_dict = ProblemSerializer(problem).data
            problem_list.append(problem_dict)

    if request.user.profile.role == 'admin':
        for problem in problems:
            problem_dict = ProblemSerializer(problem).data
            problem_list.append(problem_dict)

        for problem in problem_list:
            todo = ToDo.objects.filter(problem__id=problem['id'], accomplished=False).count()
            event = ProblemActivity.objects.filter(problem__id=problem['id'], created_on__gte=datetime.datetime.now()-datetime.timedelta(days=30)).count()
            if todo == 0 and event == 0:
                problem['multiply'] = 0
            elif todo == 0 or event == 0:
                problem['multiply'] = 1
            else:
                problem['multiply'] = todo * event

        problem_list = sorted(problem_list, key=operator.itemgetter('multiply'), reverse=True)
    else:
        for problem in problems:
            if not problem.id in problem_order.order:
                problem_dict = ProblemSerializer(problem).data
                problem_list.append(problem_dict)

    # Inactive Problems
    inactive_problems = Problem.objects.filter(
        patient=patient_user, is_active=False)
    inactive_problems_list = []
    for problem in inactive_problems:
        problem_dict = ProblemSerializer(problem).data
        inactive_problems_list.append(problem_dict)

    # Not accomplished Goals
    goals = Goal.objects.filter(patient=patient_user, accomplished=False)
    goal_list = []
    for goal in goals:
        goal_dict = GoalSerializer(goal).data
        goal_list.append(goal_dict)

    # Accomplished Goals
    completed_goals = Goal.objects.filter(
        patient=patient_user, accomplished=True)
    completed_goals_list = []
    for goal in completed_goals:
        goal_dict = GoalSerializer(goal).data
        completed_goals_list.append(goal_dict)

    # Not accomplished Todos
    pending_todos = ToDo.objects.filter(
        patient=patient_user, accomplished=False).order_by('order')
    pending_todo_list = []
    for todo in pending_todos:
        todo_dict = TodoSerializer(todo).data
        pending_todo_list.append(todo_dict)

    # Accomplished Todos
    accomplished_todos = ToDo.objects.filter(
        patient=patient_user, accomplished=True).order_by('order')
    accomplished_todo_list = []
    for todo in accomplished_todos:
        todo_dict = TodoSerializer(todo).data
        accomplished_todo_list.append(todo_dict)


    # Todos
    problem_todos = ToDo.objects.filter(
        patient=patient_user).order_by('order')
    problem_todos_list = []
    for todo in problem_todos:
        todo_dict = TodoSerializer(todo).data
        problem_todos_list.append(todo_dict)

    # encounters
    encounters = Encounter.objects.filter(
        patient=patient_user).order_by('-starttime')

    encounter_list = []
    for encounter in encounters:
        encounter_dict = EncounterSerializer(encounter).data
        encounter_list.append(encounter_dict)

    favorites = EncounterEvent.objects.filter(encounter__patient=patient_user, is_favorite=True).order_by('-datetime')

    favorites_list = []
    for favorite in favorites:
        favorite_dict = EncounterEventSerializer(favorite).data
        favorites_list.append(favorite_dict)

    # handle for hot key ctrl c
    encounter = Encounter.objects.filter(patient=patient_user).order_by('-starttime')[0]

    most_recent_encounter_events = EncounterEvent.objects.filter(encounter__patient=patient_user, encounter=encounter)

    most_recent_encounter_summarries = []
    for event in most_recent_encounter_events:
        if not "Started encounter by" in event.summary and not "Stopped encounter by" in event.summary:
            most_recent_encounter_summarries.append(event.summary)

    # Related problems
    related_problem_records = EncounterProblemRecord.objects.filter(encounter=encounter)
    related_problem_ids = [long(x.problem.id) for x in related_problem_records]

    related_problems = Problem.objects.filter(id__in=related_problem_ids)

    related_problem_holder = ProblemSerializer(
        related_problems, many=True).data


    patient_profile_dict = UserProfileSerializer(patient_profile).data

    # sharing system
    shared_patients = SharingPatient.objects.filter(sharing=patient_user).order_by('shared__first_name', 'shared__last_name')

    patients_list = []
    patients_list.append(patient_profile_dict)
    for shared_patient in shared_patients:
        user_dict = UserProfileSerializer(shared_patient.shared.profile).data
        patients_list.append(user_dict)

    sharing_patients = SharingPatient.objects.filter(shared=patient_user).order_by('sharing__first_name', 'sharing__last_name')

    sharing_patients_list = []
    for sharing_patient in sharing_patients:
        user_dict = UserProfileSerializer(sharing_patient.sharing.profile).data
        sharing_patients_list.append(user_dict)

    resp = {}
    resp['info'] = patient_profile_dict
    resp['problems'] = problem_list
    resp['goals'] = goal_list
    resp['pending_todos'] = pending_todo_list
    resp['accomplished_todos'] = accomplished_todo_list
    resp['problem_todos'] = problem_todos_list
    resp['inactive_problems'] = inactive_problems_list
    resp['timeline_problems'] = timeline_problems_list
    resp['completed_goals'] = completed_goals_list

    resp['encounters'] = encounter_list
    resp['favorites'] = favorites_list
    resp['most_recent_encounter_summarries'] = most_recent_encounter_summarries
    resp['most_recent_encounter_related_problems'] = related_problem_holder
    resp['shared_patients'] = patients_list
    resp['sharing_patients'] = sharing_patients_list
    return ajax_response(resp)


# Users
@login_required
def update_patient_summary(request, patient_id):

    resp = {}
    resp['success'] = False

    permissions = ['update_patient_profile']

    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:

        new_summary = request.POST.get('summary')
        patient = User.objects.get(id=patient_id)
        patient_profile = UserProfile.objects.get(user=patient, role='patient')
        patient_profile.summary = new_summary
        patient_profile.save()
        resp['success'] = True

    return ajax_response(resp)

@login_required
def update_patient_note(request, patient_id):

    resp = {}
    resp['success'] = False

    permissions = ['update_patient_profile']

    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:

        new_note = request.POST.get('note')
        patient = User.objects.get(id=patient_id)
        patient_profile = UserProfile.objects.get(user=patient, role='patient')
        patient_profile.note = new_note
        patient_profile.save()
        resp['success'] = True

    return ajax_response(resp)


@login_required
def update_patient_password(request, patient_id):
    resp = {}
    resp['success'] = False
    resp['message'] = ''

    permissions = ['update_patient_profile']

    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:

        old_password = request.POST.get('old_password')
        password = request.POST.get('password')
        patient = User.objects.get(id=patient_id)
        if patient.check_password(old_password):
            patient.set_password(password)
            patient.save()
            resp['success'] = True
        else:
            resp['message'] = 'Incorrect password.'
    else:
        resp['message'] = 'Not allowed'

    return ajax_response(resp)


@login_required
def update_basic_profile(request, patient_id):
    resp = {}

    resp['success'] = False

    if request.method == 'POST':
        form = UpdateBasicProfileForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            user_id = form.cleaned_data['user_id']

            if int(patient_id) == int(user_id):
                user = User.objects.get(id=user_id)
                user.first_name = first_name
                user.last_name = last_name
                user.save()

                resp['success'] = True

    return ajax_response(resp)


@login_required
def update_profile(request, patient_id):
    resp = {}
    resp['success'] = False

    if request.method == 'POST':
        form = UpdateProfileForm(request.POST, request.FILES)
        if form.is_valid():
            user_id = form.cleaned_data['user_id']
            sex = form.cleaned_data['sex']
            phone_number = form.cleaned_data['phone_number']
            summary = form.cleaned_data['summary']
            cover_image = form.cleaned_data['cover_image']
            portrait_image = form.cleaned_data['portrait_image']
            date_of_birth = form.cleaned_data['date_of_birth']

            if int(patient_id) == int(user_id):
                user = User.objects.get(id=user_id)

                user_profile = UserProfile.objects.get(user=user)

                user_profile.phone_number = phone_number
                user_profile.sex = sex
                user_profile.summary = summary
                user_profile.date_of_birth = date_of_birth

                if cover_image:
                    user_profile.cover_image = cover_image

                if portrait_image:
                    user_profile.portrait_image = portrait_image

                user_profile.save()

                if portrait_image:
                    filename = str(user_profile.portrait_image.path)
                    img = Image.open(filename)

                    if img.mode not in ('L', 'RGB'):
                        img = img.convert('RGB')

                    img.thumbnail((160,160), Image.ANTIALIAS)
                    img.save(filename)

                resp['success'] = True
                patient_profile_dict = UserProfileSerializer(user_profile).data
                resp['info'] = patient_profile_dict

    return ajax_response(resp)


@login_required
def update_patient_email(request, patient_id):
    resp = {}
    resp['success'] = False

    if request.method == 'POST':
        form = UpdateEmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user_id = form.cleaned_data['user_id']

            if int(patient_id) == int(user_id):
                user = User.objects.get(id=user_id)
                user.email = email

                user.save()

                resp['success'] = True
    return ajax_response(resp)


@login_required
def fetch_active_user(request):

    user = User.objects.get(id=request.user.id)

    user_profile = UserProfile.objects.get(user=user)
    user_role = user_profile.role

    user_profile = UserProfileSerializer(user_profile).data

    user_profile['permissions'] = ROLE_PERMISSIONS[user_role]

    resp = {}
    resp['user_profile'] = user_profile

    return ajax_response(resp)


@login_required
def staff(request):

    user = request.user
    user_profile = UserProfile.objects.get(user=user)

    content = {}
    content['user'] = user
    content['user_profile'] = user_profile

    physicians = PhysicianTeam.objects.filter(member=user)

    physician_ids = [long(x.physician.id)for x in physicians]

    patients = PatientController.objects.filter(
        physician__id__in=physician_ids)

    patients = [x.patient for x in patients]
    physicians = [x.physician for x in physicians]

    content = {}
    content['physicians'] = physicians
    content['patients'] = patients
    content['user'] = user
    content['user_profile'] = user_profile
    return render(
        request,
        'staff.html',
        content)

@login_required
def get_patient_members(request, user_id):

    user = User.objects.get(id=user_id)
    controllers = PatientController.objects.filter(patient=user)
    physician_ids = [long(x.physician.id)for x in controllers]

    physician_teams = PhysicianTeam.objects.filter(physician__id__in=physician_ids)
    member_ids = [long(x.member.id)for x in physician_teams]

    ids = physician_ids + member_ids

    users = UserProfile.objects.filter(user__id__in=ids)

    members_todos_holder = []
    for user in users:
        user_dict = UserProfileSerializer(user).data
        members_todos_holder.append(user_dict)

    resp = {}
    resp['members'] = members_todos_holder

    return ajax_response(resp)

@login_required
def get_patients_list(request):
    user_profile = UserProfile.objects.get(user=request.user)
    patients_list = []
    if user_profile.role == 'admin':
        patients = UserProfile.objects.filter(role='patient')
        for user in patients:
            user_dict = UserProfileSerializer(user).data
            patients_list.append(user_dict)

    if user_profile.role == 'patient':
        patients = UserProfile.objects.filter(role='patient').exclude(user=request.user)
        for user in patients:
            user_dict = UserProfileSerializer(user).data
            patients_list.append(user_dict)

    if user_profile.role == 'physician':
        patient_controllers = PatientController.objects.filter(physician=request.user)
        patient_ids = [long(x.patient.id) for x in patient_controllers]
        patients = UserProfile.objects.filter(user__id__in=patient_ids)
        for user in patients:
            user_dict = UserProfileSerializer(user).data
            patients_list.append(user_dict)

    if user_profile.role == 'secretary' or user_profile.role == 'mid-level' or user_profile.role == 'nurse':
        team_members = PhysicianTeam.objects.filter(member=request.user)
        physician_ids = [long(x.physician.id) for x in team_members]
        patient_controllers = PatientController.objects.filter(physician__id__in=physician_ids)
        patient_ids = [long(x.patient.id) for x in patient_controllers]
        patients = UserProfile.objects.filter(user__id__in=patient_ids)
        for user in patients:
            user_dict = UserProfileSerializer(user).data
            patients_list.append(user_dict)


    for patient in patients_list:
        patient['todo'] = ToDo.objects.filter(patient__id=patient['user']['id'], accomplished=False).count()
        patient['problem'] = Problem.objects.filter(patient__id=patient['user']['id'], is_active=True, is_controlled=False).count()
        if patient['todo'] == 0 and patient['problem'] == 0:
            patient['multiply'] = 0
        elif patient['todo'] == 0 or patient['problem'] == 0:
            patient['multiply'] = 1
        else:
            patient['multiply'] = patient['todo'] * patient['problem']

    resp = {}
    resp['patients_list'] = sorted(patients_list, key=operator.itemgetter('multiply'), reverse=True)

    return ajax_response(resp)

@login_required
def add_sharing_patient(request, patient_id, sharing_patient_id):
    resp = {}
    resp['success'] = False

    if request.method == 'POST':
        patient = User.objects.get(id=patient_id)
        to_sharing_patient = User.objects.get(id=sharing_patient_id)

        sharing_patient = SharingPatient()
        sharing_patient.sharing = to_sharing_patient
        sharing_patient.shared = patient

        sharing_patient.save()

        problems = Problem.objects.filter(patient=patient)
        for problem in problems:
            sharing_patient.problems.add(problem)

        resp['success'] = True
        resp['sharing_patient'] = UserProfileSerializer(to_sharing_patient.profile).data

    return ajax_response(resp)

@login_required
def remove_sharing_patient(request, patient_id, sharing_patient_id):
    resp = {}
    resp['success'] = False

    if request.method == 'POST':
        patient = User.objects.get(id=patient_id)
        to_sharing_patient = User.objects.get(id=sharing_patient_id)

        sharing_patient = SharingPatient.objects.get(sharing=to_sharing_patient, shared=patient)
        sharing_patient.delete()
        resp['success'] = True

    return ajax_response(resp)

@login_required
def get_sharing_patients(request, patient_id):
    resp = {}
    patient = User.objects.get(id=patient_id)
    sharing_patients = SharingPatient.objects.filter(shared=patient)

    patients_list = []
    for sharing_patient in sharing_patients:
        user_dict = UserProfileSerializer(sharing_patient.sharing.profile).data
        patients_list.append(user_dict)

    resp['sharing_patients'] = patients_list

    return ajax_response(resp)

@login_required
def get_todos_physicians(request, user_id):
    resp = {}
    staff = User.objects.get(id=user_id)

    team_members = PhysicianTeam.objects.filter(member=staff)
    physician_ids = [long(x.physician.id) for x in team_members]
    patient_controllers = PatientController.objects.filter(physician__id__in=physician_ids)
    patient_ids = [long(x.patient.id) for x in patient_controllers]

    todos = ToDo.objects.filter(patient__id__in=patient_ids, created_on__gte=datetime.datetime.now()-datetime.timedelta(hours=24)).order_by('created_on')
    todos_list = TodoSerializer(todos, many=True).data

    resp['new_generated_todos_list'] = todos_list

    physicians_list = []
    for team in team_members:
        user_dict = UserProfileSerializer(team.physician.profile).data
        physicians_list.append(user_dict)

    resp['new_generated_physicians_list'] = physicians_list

    return ajax_response(resp)

@login_required
def user_info(request, user_id):
    user = User.objects.get(id=user_id)
    user_profile = UserProfile.objects.get(user=user)

    user_profile_dict = UserProfileSerializer(user_profile).data

    resp = {}
    resp['success'] = False
    resp['user_profile'] = user_profile_dict
    return ajax_response(resp)