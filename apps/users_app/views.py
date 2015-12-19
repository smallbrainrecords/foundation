#!/usr/bin/env python
try:
    from PIL import Image, ImageOps
except ImportError:
    import Image
    import ImageOps

from common.views import *

from emr.models import UserProfile, Problem
from emr.models import Goal, ToDo
from emr.models import Encounter, Sharing

from emr.models import PhysicianTeam, PatientController

from problems_app.serializers import ProblemSerializer
from goals_app.serializers import GoalSerializer
from .serializers import UserProfileSerializer
from todo_app.serializers import TodoSerializer
from encounters_app.serializers import EncounterSerializer

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

            if role in ['admin', 'physician']:
                # Manage Users
                return HttpResponseRedirect('/project/admin')
            if role == 'patient':
                # Manage Patient
                return HttpResponseRedirect('/u/patient/manage/%s/' % user.id)
            if role in ['secretary', 'nurse', 'mid-level']:
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

    # Active Problems
    problems = Problem.objects.filter(patient=patient_user, is_active=True)
    problem_list = []
    for problem in problems:
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
        patient=patient_user, accomplished=False)
    pending_todo_list = []
    for todo in pending_todos:
        todo_dict = TodoSerializer(todo).data
        pending_todo_list.append(todo_dict)

    # Accomplished Todos
    accomplished_todos = ToDo.objects.filter(
        patient=patient_user, accomplished=True)
    accomplished_todo_list = []
    for todo in accomplished_todos:
        todo_dict = TodoSerializer(todo).data
        accomplished_todo_list.append(todo_dict)

    encounters = Encounter.objects.filter(
        patient=patient_user).order_by('-starttime')

    encounter_list = []
    for encounter in encounters:
        encounter_dict = EncounterSerializer(encounter).data
        encounter_list.append(encounter_dict)

    patient_profile_dict = UserProfileSerializer(patient_profile).data

    resp = {}
    resp['info'] = patient_profile_dict
    resp['problems'] = problem_list
    resp['goals'] = goal_list
    resp['pending_todos'] = pending_todo_list
    resp['accomplished_todos'] = accomplished_todo_list
    resp['inactive_problems'] = inactive_problems_list
    resp['completed_goals'] = completed_goals_list

    resp['encounters'] = encounter_list
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
