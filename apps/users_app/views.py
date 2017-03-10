#!/usr/bin/env python
from dateutil.relativedelta import relativedelta

try:
    from PIL import Image, ImageOps
except ImportError:
    import Image
    import ImageOps
import operator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from django.db.models import Q
from common.views import *
# from django.shortcuts import render
from emr.models import UserProfile, Problem, TaggedToDoOrder, Medication, MEDICATION_BLEEDING_RISK, GeneralSetting, \
    Document
from emr.models import Goal, ToDo
from emr.models import Encounter, Sharing, EncounterEvent, EncounterProblemRecord

from emr.models import PhysicianTeam, PatientController, ProblemOrder, ProblemActivity
from emr.models import SharingPatient, CommonProblem
from emr.models import ProblemNote
from emr.models import MyStoryTab, MyStoryTextComponent

from problems_app.serializers import ProblemSerializer, CommonProblemSerializer
from goals_app.serializers import GoalSerializer
from .serializers import UserProfileSerializer
from todo_app.serializers import TodoSerializer
from encounters_app.serializers import EncounterSerializer, EncounterEventSerializer

from .forms import LoginForm, RegisterForm, UpdateBasicProfileForm, UpdateProfileForm, UpdateEmailForm

import datetime

from emr.manage_patient_permissions import ROLE_PERMISSIONS

from emr.manage_patient_permissions import check_access


def permissions_accessed(user, obj_user_id):
    """
    Check whether or not clinical staff(s) can control patient
    :param user: Clinical staff
    :param obj_user_id: Patient
    :return:
    """
    permitted = False

    user_profile = UserProfile.objects.get(user=user)
    if user_profile.role == 'admin':
        permitted = True

    elif user_profile.role == 'patient':
        if user.id == obj_user_id:
            permitted = True
        sharing_patients = SharingPatient.objects.filter(shared_id=obj_user_id)
        patient_ids = [x.sharing.id for x in sharing_patients]
        if user.id in patient_ids:
            permitted = True

    elif user_profile.role == 'physician':
        patient_controllers = PatientController.objects.filter(physician=user)
        patient_ids = [x.patient.id for x in patient_controllers]
        patient_ids.append(user.id)
        if obj_user_id in patient_ids:
            permitted = True

    elif user_profile.role in ('secretary', 'mid-level', 'nurse'):
        team_members = PhysicianTeam.objects.filter(member=user)
        physician_ids = [x.physician.id for x in team_members]
        patient_controllers = PatientController.objects.filter(physician__id__in=physician_ids)
        patient_ids = [x.patient.id for x in patient_controllers]
        patient_ids.append(user.id)
        if obj_user_id in patient_ids:
            permitted = True

    return permitted


def is_patient(user):
    try:
        profile = UserProfile.objects.get(user=user)
        return profile.role == 'patient'
    except UserProfile.DoesNotExist:
        return False


def login_user(request):
    if request.method == "GET":
        return render(request, 'users/login.html', {})
    elif request.method == 'POST':
        logout(request)
        form = LoginForm(request.POST)

        errors = []
        if not form.is_valid():
            errors.append('Please fill valid data.')
            content = {'login_errors': errors, 'form': form}
            return render(request, 'users/login.html', content)

        username = form.cleaned_data['username']
        password = form.cleaned_data['password']

        user = authenticate(username=username, password=password)
        if user and user.is_active:
            login(request, user)
            return HttpResponseRedirect('/u/home/')
        else:
            if not user:
                errors.append('Incorrect username or password.')
            elif not user.is_active:
                errors.append('User is not verified or active.')
            content = {'login_errors': errors, 'form': form}
            return render(request, 'users/login.html', content)


def logout_user(request):
    logout(request.user)
    return HttpResponseRedirect('/u/login/')


def register_user(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        errors = []
        if not form.is_valid():
            errors.append('Please fill data')
            return render(request, 'users/login.html', {"register_form": form, "register_errors": errors})

        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        verify_password = form.cleaned_data['verify_password']
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']

        if len(password) <= 2 or password != verify_password:
            errors.append('Passwords must match')
            return render(request, 'users/login.html', {"register_form": form, "register_errors": errors})

        user_exists = User.objects.filter(Q(email=email) | Q(username=email)).exists()
        if user_exists:
            errors.append('User with same email or username already exists')
            return render(request, 'users/login.html', {"register_form": form, "register_errors": errors})

        current = datetime.datetime.now()
        user = User(username=email, email=email, first_name=first_name,
                    last_name=last_name, last_login=current)
        user.set_password(password)
        user.save()

        user = authenticate(username=email, password=password)
        login(request, user)
        return HttpResponseRedirect('/u/home')


@login_required
def home(request):
    if request.method == 'GET':
        user = request.user
        user_profile = UserProfile.objects.filter(user=user).first()

        if not user_profile:
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

        role = user_profile.role
        if role == 'admin':
            # Manage Users
            return HttpResponseRedirect('/project/admin')
        elif role == 'patient':
            # Manage Patient
            return HttpResponseRedirect('/u/patient/manage/%s/' % user.id)
        elif role in ['secretary', 'nurse', 'mid-level', 'physician']:
            return HttpResponseRedirect('/u/staff/')

        return HttpResponse('Something went wrong !')


# Users
@login_required
def manage_patient(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return HttpResponse('Something went wrong !')
    actor_profile = UserProfile.objects.get(user=request.user)
    patient_profile = UserProfile.objects.get(user=user)

    # Allowed viewers
    # The patient, admin/physician, and other patients the patient has shared
    allowed = False
    allowed = check_access(patient_profile.user, actor_profile)

    if not allowed:
        return HttpResponse("Not allowed")
    if not is_patient(user):
        return HttpResponse("Error: this user isn't a patient")

    context = {}

    context['patient'] = user
    context['user_role'] = actor_profile.role
    context['patient_profile'] = patient_profile

    context = RequestContext(request, context)
    return render_to_response("manage_patient.html", context)


# Users
# TODO: Clean up later
@login_required
def get_patient_info(request, patient_id):
    resp = {}
    patient_user = User.objects.get(id=patient_id)
    patient_profile = UserProfile.objects.get(user=patient_user)

    # add Fit and Well: 102499006 by default
    if not Problem.objects.filter(patient=patient_user, concept_id='102499006'):
        problem = Problem()
        problem.concept_id = '102499006'
        problem.problem_name = 'Fit and well (finding)'
        problem.patient = patient_user
        problem.save()

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
            event = ProblemActivity.objects.filter(problem__id=problem['id'],
                                                   created_on__gte=datetime.datetime.now() - datetime.timedelta(
                                                       days=30)).count()
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

    inactive_problems = Problem.objects.filter(patient=patient_user, is_active=False)
    goals = Goal.objects.filter(patient=patient_user, accomplished=False)
    completed_goals = Goal.objects.filter(patient=patient_user, accomplished=True)
    encounters = Encounter.objects.filter(patient=patient_user).order_by('-starttime')
    favorites = EncounterEvent.objects.filter(encounter__patient=patient_user, is_favorite=True).order_by('-datetime')

    # Retrieve most recent encounter information
    most_recent_encounter_summaries = []
    most_recent_encounter_documents_holder = []
    related_problem_holder = []
    encounter = Encounter.objects.filter(patient=patient_user).order_by("-starttime").first()
    if encounter:
        # Encounter's event summaries
        most_recent_encounter_events = EncounterEvent.objects.filter(encounter__patient=patient_user,
                                                                     encounter=encounter)

        for event in most_recent_encounter_events:
            if not "Started encounter by" in event.summary and not "Stopped encounter by" in event.summary:
                most_recent_encounter_summaries.append(event.summary)

        # Encounter's document
        for document in encounter.encounter_document.all():
            most_recent_encounter_documents_holder.append({
                'name': document.component.__str__(),
                'value': '%g' % float(document.value_quantity),
                'effective': document.effective_datetime.isoformat()
            })

        # Encounter's related problems
        related_problem_records = EncounterProblemRecord.objects.filter(encounter=encounter)
        related_problem_ids = [x.problem.id for x in related_problem_records]

        related_problems = Problem.objects.filter(id__in=related_problem_ids)
        related_problem_holder = ProblemSerializer(related_problems, many=True).data

    # sharing system
    shared_patients = SharingPatient.objects.filter(sharing=patient_user).order_by('shared__first_name',
                                                                                   'shared__last_name')
    patients_list = []
    for shared_patient in shared_patients:
        user_dict = UserProfileSerializer(shared_patient.shared.profile).data
        patients_list.append(user_dict)

    sharing_patients = SharingPatient.objects.filter(shared=patient_user).order_by('sharing__first_name',
                                                                                   'sharing__last_name')
    sharing_patients_list = []
    for sharing_patient in sharing_patients:
        user_dict = UserProfileSerializer(sharing_patient.sharing.profile).data
        user_dict['problems'] = [x.id for x in sharing_patient.problems.all()]
        user_dict['is_my_story_shared'] = sharing_patient.is_my_story_shared
        sharing_patients_list.append(user_dict)

    # common problems
    acutes = CommonProblem.objects.filter(author=request.user, problem_type="acute")
    chronics = CommonProblem.objects.filter(author=request.user, problem_type="chronic")

    resp['info'] = UserProfileSerializer(patient_profile).data
    resp['problems'] = problem_list
    resp['goals'] = GoalSerializer(goals, many=True).data
    resp['inactive_problems'] = ProblemSerializer(inactive_problems, many=True).data
    resp['completed_goals'] = GoalSerializer(completed_goals, many=True).data
    resp['encounters'] = EncounterSerializer(encounters, many=True).data
    resp['favorites'] = EncounterEventSerializer(favorites, many=True).data
    resp['most_recent_encounter_summaries'] = most_recent_encounter_summaries
    resp['most_recent_encounter_related_problems'] = related_problem_holder
    resp['most_recent_encounter_documents'] = most_recent_encounter_documents_holder
    resp['shared_patients'] = patients_list
    resp['sharing_patients'] = sharing_patients_list
    resp['acutes_list'] = CommonProblemSerializer(acutes, many=True).data
    resp['chronics_list'] = CommonProblemSerializer(chronics, many=True).data
    resp['bleeding_risk'] = Medication.objects.filter(current=True).filter(
        concept_id__in=MEDICATION_BLEEDING_RISK).filter(patient=patient_profile).exists()
    return ajax_response(resp)


@login_required
def get_timeline_info(request, patient_id):
    # Timeline Problems
    timeline_problems = Problem.objects.filter(patient_id=patient_id)
    resp = {}
    resp['timeline_problems'] = ProblemSerializer(timeline_problems, many=True).data
    return ajax_response(resp)


@login_required
def get_patient_todos_info(request, patient_id):
    todos = ToDo.objects.filter(patient_id=patient_id).order_by("order")
    pending_todos = [todo for todo in todos if todo.accomplished is False]
    accomplished_todos = [todo for todo in todos if todo.accomplished is True]
    resp = {}
    resp['pending_todos'] = TodoSerializer(pending_todos, many=True).data
    resp['accomplished_todos'] = TodoSerializer(accomplished_todos, many=True).data
    resp['problem_todos'] = TodoSerializer(todos, many=True).data
    return ajax_response(resp)


# Users
@permissions_required(["update_patient_profile"])
@login_required
def update_patient_summary(request, patient_id):
    new_summary = request.POST.get('summary')
    patient_profile = UserProfile.objects.get(user_id=patient_id, role='patient')
    patient_profile.summary = new_summary
    patient_profile.save()
    resp = {}
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["update_patient_profile"])
@login_required
def update_patient_note(request, patient_id):
    resp = {}
    new_note = request.POST.get('note')
    patient_profile = UserProfile.objects.get(user_id=patient_id, role='patient')
    patient_profile.note = new_note
    patient_profile.save()
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["update_patient_profile"])
@login_required
def update_patient_password(request, patient_id):
    resp = {}
    resp['success'] = False
    resp['message'] = ''

    old_password = request.POST.get('old_password')
    password = request.POST.get('password')
    patient = User.objects.get(id=patient_id)
    if patient.check_password(old_password):
        patient.set_password(password)
        patient.save()
        resp['success'] = True
    else:
        resp['message'] = 'Incorrect password.'

    return ajax_response(resp)


@login_required
@api_view(["POST"])
def update_basic_profile(request, patient_id):
    resp = {}
    resp['success'] = False

    form = UpdateBasicProfileForm(request.POST)
    if not form.is_valid():
        return ajax_response(resp)

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
@api_view(["POST"])
def update_profile(request, patient_id):
    resp = {'success': False}

    form = UpdateProfileForm(request.POST, request.FILES)
    if not form.is_valid():
        return ajax_response(resp)

    user_id = form.cleaned_data['user_id']
    sex = form.cleaned_data['sex']
    phone_number = form.cleaned_data['phone_number']
    summary = form.cleaned_data['summary']
    cover_image = form.cleaned_data['cover_image']
    portrait_image = form.cleaned_data['portrait_image']
    date_of_birth = form.cleaned_data['date_of_birth']

    if int(patient_id) != int(user_id):
        return ajax_response(resp)

    # TODO: Just doing form.save() should work.
    user_profile = UserProfile.objects.get(user_id=user_id)
    if phone_number:
        user_profile.phone_number = phone_number
    if sex:
        user_profile.sex = sex
    if summary:
        user_profile.summary = summary
    if date_of_birth:
        user_profile.date_of_birth = date_of_birth

    if cover_image:
        user_profile.cover_image = cover_image

    if portrait_image:
        user_profile.portrait_image = portrait_image
    user_profile.save()

    resp['success'] = True
    resp['info'] = UserProfileSerializer(user_profile).data
    return ajax_response(resp)


@login_required
@api_view(["POST"])
def update_patient_email(request, patient_id):
    resp = {'success': False}
    form = UpdateEmailForm(request.POST)
    if not form.is_valid():
        return ajax_response(resp)
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
    resp = {}
    user_profile = UserProfile.objects.get(user=request.user)

    user_profile_serialized = UserProfileSerializer(user_profile).data
    user_profile_serialized['permissions'] = ROLE_PERMISSIONS[user_profile.role]

    resp['user_profile'] = user_profile_serialized
    return ajax_response(resp)


@login_required
def staff(request):
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    if user_profile.role == 'patient' or user_profile.role == 'admin':
        return HttpResponseRedirect('/')
    physicians = PhysicianTeam.objects.filter(member=user)

    physician_ids = [x.physician.id for x in physicians]
    patients = PatientController.objects.filter(physician__id__in=physician_ids)
    patient_ids = [x.patient.id for x in patients]
    patients = User.objects.filter(id__in=patient_ids).filter(is_active=True)

    physicians = [x.physician for x in physicians]

    content = {}
    content['physicians'] = physicians
    content['patients'] = patients
    content['user'] = user
    content['user_profile'] = user_profile
    return render(request, 'staff.html', content)


@login_required
def get_patient_members(request, user_id):
    controllers = PatientController.objects.filter(patient_id=user_id)
    physician_ids = [x.physician.id for x in controllers]

    physician_teams = PhysicianTeam.objects.filter(physician__id__in=physician_ids)
    member_ids = [x.member.id for x in physician_teams]
    ids = physician_ids + member_ids
    users = UserProfile.objects.filter(user__id__in=ids)

    resp = {}
    resp['members'] = UserProfileSerializer(users, many=True).data
    return ajax_response(resp)


@login_required
def get_patients_list(request):
    user_profile = UserProfile.objects.get(user=request.user)
    if user_profile.role == 'admin':
        patients = UserProfile.objects.filter(role='patient').filter(user__is_active=True)

    elif user_profile.role == 'patient':
        patients = UserProfile.objects.filter(role='patient').exclude(user=request.user).filter(user__is_active=True)

    elif user_profile.role == 'physician':
        patient_controllers = PatientController.objects.filter(physician=request.user)
        patient_ids = [x.patient.id for x in patient_controllers]
        patients = UserProfile.objects.filter(user__id__in=patient_ids).filter(user__is_active=True)

    elif user_profile.role in ('secretary', 'mid-level', 'nurse'):
        team_members = PhysicianTeam.objects.filter(member=request.user)
        physician_ids = [x.physician.id for x in team_members]
        patient_controllers = PatientController.objects.filter(physician__id__in=physician_ids)
        patient_ids = [x.patient.id for x in patient_controllers]
        patients = UserProfile.objects.filter(user__id__in=patient_ids).filter(user__is_active=True)

    patients_list = UserProfileSerializer(patients, many=True).data
    for patient in patients_list:
        todo_count = ToDo.objects.filter(patient__id=patient['user']['id'], accomplished=False).count()
        problem_count = Problem.objects.filter(patient__id=patient['user']['id'], is_active=True,
                                               is_controlled=False).count()
        six_weeks_earlier = datetime.datetime.now() - relativedelta(weeks=6)
        encounter_count = Encounter.objects.filter(patient__id=patient['user']['id'],
                                                   starttime__gte=six_weeks_earlier).count()

        patient["encounter"] = encounter_count
        patient["todo"] = todo_count
        patient["problem"] = problem_count
        patient['multiply'] = (todo_count if todo_count != 0 else 1) * (problem_count if problem_count != 0 else 1) * (
        encounter_count if encounter_count != 0 else 1)

    resp = {'patients_list': sorted(patients_list, key=operator.itemgetter('multiply'), reverse=True)}
    return ajax_response(resp)


@permissions_required(["add_sharing_patient"])
@login_required
@api_view(["POST"])
def add_sharing_patient(request, patient_id, sharing_patient_id):
    resp = {}
    to_sharing_patient_profile = UserProfile.objects.get(user_id=sharing_patient_id)
    sharing_patient = SharingPatient.objects.create(sharing_id=sharing_patient_id, shared_id=patient_id)

    problems = Problem.objects.filter(patient_id=patient_id)
    sharing_patient.problems.add(*problems)
    sharing_patient.save()

    resp['success'] = True
    resp['sharing_patient'] = UserProfileSerializer(to_sharing_patient_profile).data
    return ajax_response(resp)


@permissions_required(["remove_sharing_patient"])
@login_required
@api_view(["POST"])
def remove_sharing_patient(request, patient_id, sharing_patient_id):
    sharing_patient = SharingPatient.objects.get(sharing_id=sharing_patient_id, shared_id=patient_id)
    sharing_patient.delete()
    resp = {}
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["add_sharing_patient"])
@login_required
@api_view(["POST"])
def change_sharing_my_story(request, patient_id, sharing_patient_id):
    sharing_patient = SharingPatient.objects.get(sharing_id=sharing_patient_id, shared_id=patient_id)
    sharing_patient.is_my_story_shared = not sharing_patient.is_my_story_shared
    sharing_patient.save()
    resp = {}
    resp['success'] = True
    return ajax_response(resp)


@login_required
def get_sharing_patients(request, patient_id):
    resp = {}
    sharing_patients = SharingPatient.objects.filter(shared_id=patient_id)

    patients_list = []
    for sharing_patient in sharing_patients:
        user_dict = UserProfileSerializer(sharing_patient.sharing.profile).data
        patients_list.append(user_dict)
    resp['sharing_patients'] = patients_list
    return ajax_response(resp)


@login_required
def get_todos_physicians(request, user_id):
    resp = {}
    team_members = PhysicianTeam.objects.filter(member_id=user_id)
    physician_ids = [x.physician.id for x in team_members]
    patient_controllers = PatientController.objects.filter(physician__id__in=physician_ids)
    patient_ids = [x.patient.id for x in patient_controllers]

    todos = ToDo.objects.filter(accomplished=False, patient__id__in=patient_ids,
                                created_on__gte=datetime.datetime.now() - datetime.timedelta(hours=24)
                                ).order_by('created_on')

    resp['new_generated_todos_list'] = TodoSerializer(todos, many=True).data

    physicians_list = []
    for team in team_members:
        user_dict = UserProfileSerializer(team.physician.profile).data
        physicians_list.append(user_dict)

    resp['new_generated_physicians_list'] = physicians_list
    return ajax_response(resp)


@login_required
def user_info(request, user_id):
    user_profile = UserProfile.objects.get(user_id=user_id)
    resp = {}
    resp['success'] = True
    resp['user_profile'] = UserProfileSerializer(user_profile).data
    return ajax_response(resp)


@login_required
@api_view(["POST"])
def search(request, user_id):
    user = User.objects.get(id=user_id)
    actor_profile = UserProfile.objects.get(user=request.user)
    patient_profile = UserProfile.objects.get(user=user)

    # Allowed viewers
    # The patient, admin/physician, and other patients the patient has shared
    allowed = False
    allowed = check_access(patient_profile.user, actor_profile)

    if not allowed:
        return HttpResponse("Not allowed")
    if not is_patient(user):
        return HttpResponse("Error: this user isn't a patient")

    patient_ids = []
    if actor_profile.role == 'admin':
        patients = UserProfile.objects.filter(role='patient')
        patient_ids = [x.user.id for x in patients]
    elif actor_profile.role == 'physician':
        patient_controllers = PatientController.objects.filter(physician=request.user)
        patient_ids = [x.patient.id for x in patient_controllers]
    elif actor_profile.role in ('secretary', 'mid-level', 'nurse'):
        team_members = PhysicianTeam.objects.filter(member=request.user)
        physician_ids = [x.physician.id for x in team_members]
        patient_controllers = PatientController.objects.filter(physician__id__in=physician_ids)
        patient_ids = [x.patient.id for x in patient_controllers]

    context = {}
    query = request.POST.get("query", None)
    if query:
        notes = ProblemNote.objects.filter(note__icontains=query, problem__patient=user)
        context['notes'] = notes

        goals = Goal.objects.filter(goal__icontains=query, patient=user)
        context['goals'] = goals

        todos = ToDo.objects.filter(todo__icontains=query, patient=user)
        context['todos'] = todos

        summaries = EncounterEvent.objects.filter(summary__icontains=query, encounter__patient=user)
        context['summaries'] = summaries

        tabs = MyStoryTab.objects.filter(name__icontains=query, patient=user)
        context['tabs'] = tabs

        text_components = MyStoryTextComponent.objects.filter(Q(name__icontains=query), patient=user)
        context['text_components'] = text_components

        documents = Document.objects.filter(Q(document__icontains=query), patient=user.profile)
        context['documents'] = documents
        if request.user.profile.role is not 'patient':
            patients = UserProfile.objects.filter(role='patient').filter(
                Q(user__first_name__icontains=query)
                | Q(user__last_name__icontains=query)
            ).filter(user_id__in=patient_ids)
            context['patients'] = patients

    context['patient'] = user
    context['user_role'] = actor_profile.role
    context['patient_profile'] = patient_profile

    context = RequestContext(request, context)
    return render_to_response("patient_search.html", context)


@login_required
@api_view(["POST"])
def staff_search(request):
    user_profile = UserProfile.objects.get(user=request.user)
    if user_profile.role == 'patient':
        return HttpResponse("Not allowed")
    patient_ids = []
    if user_profile.role == 'admin':
        patients = UserProfile.objects.filter(role='patient')
        patient_ids = [x.user.id for x in patients]
    elif user_profile.role == 'physician':
        patient_controllers = PatientController.objects.filter(physician=request.user)
        patient_ids = [x.patient.id for x in patient_controllers]
    elif user_profile.role in ('secretary', 'mid-level', 'nurse'):
        team_members = PhysicianTeam.objects.filter(member=request.user)
        physician_ids = [x.physician.id for x in team_members]
        patient_controllers = PatientController.objects.filter(physician__id__in=physician_ids)
        patient_ids = [x.patient.id for x in patient_controllers]

    context = {}
    query = request.POST.get("query", None)
    if query:
        notes = ProblemNote.objects.filter(note__icontains=query, problem__patient__id__in=patient_ids)
        context['notes'] = notes

        goals = Goal.objects.filter(goal__icontains=query, patient__id__in=patient_ids)
        context['goals'] = goals

        todos = ToDo.objects.filter(todo__icontains=query, patient__id__in=patient_ids)
        context['todos'] = todos

        summaries = EncounterEvent.objects.filter(summary__icontains=query, encounter__patient__id__in=patient_ids)
        context['summaries'] = summaries

        tabs = MyStoryTab.objects.filter(name__icontains=query, patient__id__in=patient_ids)
        context['tabs'] = tabs

        text_components = MyStoryTextComponent.objects.filter(Q(name__icontains=query), patient__id__in=patient_ids)
        context['text_components'] = text_components

        documents = Document.objects.filter(Q(document__icontains=query))
        context['documents'] = documents

        if request.user.profile.role is not 'patient':
            patients = UserProfile.objects.filter(role='patient').filter(
                Q(user__first_name__icontains=query)
                | Q(user__last_name__icontains=query)
            ).filter(user_id__in=patient_ids)
            context['patients'] = patients
    context['user_profile'] = user_profile

    context = RequestContext(request, context)
    return render_to_response("staff_search.html", context)


@login_required
def update_last_access_tagged_todo(request, user_id):
    """
    Update last time user access the tagged todo frame.
    Mostly used within staff page
    :param request:
    :param user_id:
    :return:
    """
    resp = {'success': False}
    user_profile = UserProfile.objects.get(user_id=user_id)
    user_profile.last_access_tagged_todo = datetime.datetime.now()
    user_profile.save()

    # Update all newly tagged todo to viewed todo
    # TaggedToDoOrder.objects.filter(user_id=user_profile.user_id).filter(status=0).update(status=1)

    resp['success'] = True

    return ajax_response(resp)


@login_required
def get_general_setting(request):
    resp = {'success': False}
    data = {}
    settings = GeneralSetting.objects.all()
    for setting in settings:
        data[setting.setting_key] = setting.setting_value

    resp['settings'] = data
    return ajax_response(resp)


@login_required
def update_general_setting(request):
    resp = {'success': False}
    json_body = json.loads(request.body)
    key = json_body.get('setting_key')
    value = json_body.get('setting_value')

    if request.user.profile.role in ['admin', 'physician']:
        GeneralSetting.objects.filter(setting_key=key).update(setting_value=value)
        resp['success'] = True

    return ajax_response(resp)
