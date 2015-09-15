from common.views import *

from django.contrib.auth.models import User
from emr.models import UserProfile

from users_app.serializers import UserProfileSerializer
import logging
from .forms import UpdateProfileForm, UpdateBasicProfileForm
from .forms import UpdateEmailForm, UpdatePasswordForm
from .forms import CreateUserForm, AssignPhysicianMemberForm

import datetime

from emr.models import PatientController, PhysicianTeam


@login_required
def home(request):

    content = {}

    return render(
        request,
        'project_admin/home.html',
        content)


@login_required
def list_registered_users(request):

    actor = request.user
    actor_profile = UserProfile.objects.get(user=actor)

    if actor_profile.role == 'physician':

        controlled_patients = PatientController.objects.filter(physician=actor)
        patients_ids = [long(x.patient.id) for x in controlled_patients]
        user_profiles = UserProfile.objects.filter(user__id__in=patients_ids)

    if actor_profile.role == 'admin':

        user_profiles = UserProfile.objects.all()

    user_profiles_holder = UserProfileSerializer(user_profiles, many=True).data

    return ajax_response(user_profiles_holder)


@login_required
def list_unregistered_users(request):

    users = []
    for user in User.objects.all():
        try:
            UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            users.append({
                'id': user.id,
                'username': user.username,
                'full_name': user.get_full_name()})
    return ajax_response(users)


@login_required
def user_info(request, user_id):
    user = User.objects.get(id=user_id)
    user_profile = UserProfile.objects.get(user=user)

    user_profile_dict = UserProfileSerializer(user_profile).data

    resp = {}
    resp['success'] = False
    resp['user_profile'] = user_profile_dict
    return ajax_response(resp)


@login_required
def approve_user(request):
    success = False

    user_id = request.POST.get('id')
    role = request.POST.get('role')

    try:
        user = User.objects.get(id=long(user_id))
    except User.DoesNotExist:
        user = None

    if user is not None and role in ['physician', 'admin', 'patient']:
        user_profile = UserProfile(user=user, role=role)
        user_profile.save()

        if role == 'admin':
            user.is_superuser = True
            user.is_staff = True
            user.save()

        success = True
        msg = 'User was assigned given role and made active'

    resp = {}
    resp['success'] = success
    resp['msg'] = msg
    return ajax_response(resp)


@login_required
def update_profile(request):

    resp = {}
    resp['success'] = False

    if request.method == 'POST':
        form = UpdateProfileForm(request.POST, request.FILES)
        if form.is_valid():
            user_id = form.cleaned_data['user_id']
            sex = form.cleaned_data['sex']
            role = form.cleaned_data['role']
            phone_number = form.cleaned_data['phone_number']
            summary = form.cleaned_data['summary']
            cover_image = form.cleaned_data['cover_image']
            portrait_image = form.cleaned_data['portrait_image']
            date_of_birth = form.cleaned_data['date_of_birth']

            user = User.objects.get(id=user_id)

            user_profile = UserProfile.objects.get(user=user)

            user_profile.phone_number = phone_number
            user_profile.sex = sex
            user_profile.role = role
            user_profile.summary = summary
            user_profile.date_of_birth = date_of_birth

            if cover_image:
                user_profile.cover_image = cover_image

            if portrait_image:
                user_profile.portrait_image = portrait_image

            user_profile.save()

            resp['success'] = True

    return ajax_response(resp)


@login_required
def update_basic_profile(request):

    resp = {}

    resp['success'] = False

    if request.method == 'POST':
        form = UpdateBasicProfileForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            user_id = form.cleaned_data['user_id']

            user = User.objects.get(id=user_id)
            user.first_name = first_name
            user.last_name = last_name
            user.save()

            resp['success'] = True

    return ajax_response(resp)


@login_required
def update_email(request):
    resp = {}
    resp['success'] = False

    if request.method == 'POST':
        form = UpdateEmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user_id = form.cleaned_data['user_id']

            user = User.objects.get(id=user_id)
            user.email = email

            user.save()

            resp['success'] = True
    return ajax_response(resp)


@login_required
def update_password(request):
    resp = {}
    resp['success'] = False
    if request.method == 'POST':
        form = UpdatePasswordForm(request.POST)
        if form.is_valid():
            user_id = form.cleaned_data['user_id']
            new_password = form.cleaned_data['new_password']
            verify_password = form.cleaned_data['verify_password']

            if len(new_password) > 3 and new_password == verify_password:
                user = User.objects.get(id=user_id)
                user.set_password(new_password)
                user.save()

            resp['success'] = True

    return ajax_response(resp)


@login_required
def create_user(request):
    errors = []
    actor = request.user
    msg = 'Operation Failed'
    success = False
    try:
        actor_profile = UserProfile.objects.get(user=actor)
    except UserProfile.DoesNotExist:
        actor_profile = None

    if request.method == 'POST':

        form = CreateUserForm(request.POST, request.FILES)

        if form.is_valid():
            # logging.error('valid form')
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            role = form.cleaned_data['role']
            password = form.cleaned_data['password']
            verify_password = form.cleaned_data['verify_password']
            date_of_birth = form.cleaned_data['date_of_birth']
            sex = form.cleaned_data['sex']
            phone_number = form.cleaned_data['phone_number']
            cover_image = form.cleaned_data['cover_image']
            portrait_image = form.cleaned_data['portrait_image']
            summary = form.cleaned_data['summary']

            user_check = pass_match_check = pass_length_check = False

            if not User.objects.filter(username=username).exists():
                user_check = True
            else:
                errors.append('Username already exists.')

            if password == verify_password:
                pass_match_check = True
            else:
                errors.append('Password is not matching.')

            if len(password) > 2:
                pass_length_check = True
            else:
                errors.append('Password should be at least 3 characters.')

            if pass_match_check and pass_length_check and user_check:

                logging.error('Creating User')

                try:
                    current_time = datetime.datetime.now()
                    new_user = User.objects.create(
                        first_name=first_name,
                        last_name=last_name,
                        username=username,
                        email=email,
                        last_login=current_time,
                        date_joined=current_time)
                    new_user.set_password(password)
                    new_user.save()
                except Exception as e:
                    raise e
                    logging.error(e)

                    new_user = None

                if new_user is not None:

                    user_profile = UserProfile(
                        user=new_user,
                        role=role,
                        summary=summary,
                        sex=sex,
                        date_of_birth=date_of_birth,
                        phone_number=phone_number)

                    if cover_image:
                        user_profile.cover_image = cover_image

                    if portrait_image:
                        user_profile.portrait_image = portrait_image

                    user_profile.save()

                    if actor_profile is not None and role == 'patient':
                        if actor_profile.role == 'physician':
                            patient_controller = PatientController(
                                patient=new_user,
                                physician=actor,
                                author=True)
                            patient_controller.save()

                    success = True

        else:
            for error in form.errors.items():
                errors.append(error)
            msg = 'Please fill valid data!'
    resp = {}
    resp['success'] = success
    resp['msg'] = msg
    resp['errors'] = errors
    return ajax_response(resp)


@login_required
def list_patient_physicians(request):

    patient_id = request.GET.get('patient_id')

    physicians_list = []

    try:
        patient = User.objects.get(id=patient_id)
        controllers = PatientController.objects.filter(patient=patient)

        physician_ids = [long(x.physician.id) for x in controllers]
        physicians = UserProfile.objects.filter(user__id__in=physician_ids)

        physicians_list = UserProfileSerializer(physicians, many=True).data
    except User.DoesNotExist as e:
        resp['error'] = str(e)

    resp = {}
    resp['success'] = True
    resp['physicians'] = physicians_list

    return ajax_response(resp)


@login_required
def fetch_physician_data(request):

    success = False

    physician_id = request.GET.get('physician_id')
    physician = User.objects.get(id=physician_id)

    team_members = PhysicianTeam.objects.filter(physician=physician)
    user_ids = [long(x.member.id) for x in team_members]

    user_profiles = UserProfile.objects.all().exclude(
        Q(role='physician') | Q(role='patient'))

    nurses = []
    nurses_list = []
    secretaries = []
    secretaries_list = []
    mid_level_staffs = []
    mid_level_staffs_list = []

    for user_profile in user_profiles:
        profile_dict = UserProfileSerializer(user_profile).data
        if user_profile.user.id in user_ids:
            if user_profile.role == 'nurse':
                nurses.append(profile_dict)
            if user_profile.role == 'mid-level':
                mid_level_staffs.append(profile_dict)
            if user_profile.role == 'secretary':
                secretaries.append(profile_dict)
        else:
            if user_profile.role == 'nurse':
                nurses_list.append(profile_dict)
            if user_profile.role == 'mid-level':
                mid_level_staffs_list.append(profile_dict)
            if user_profile.role == 'secretary':
                secretaries_list.append(profile_dict)

    patients = PatientController.objects.filter(physician=physician)
    patient_ids = [long(x.patient.id) for x in patients]

    patient_profiles = UserProfile.objects.filter(user__id__in=patient_ids)
    patient_profiles_dict = UserProfileSerializer(
        patient_profiles, many=True).data

    unassigned_patient_profiles = UserProfile.objects.filter(
        role='patient').exclude(user__id__in=patient_ids)
    unassigned_patients_dict = UserProfileSerializer(
        unassigned_patient_profiles, many=True).data

    success = True

    resp = {}
    resp['success'] = success
    resp['patients'] = patient_profiles_dict
    team = {}
    team['nurses'] = nurses
    team['secretaries'] = secretaries
    team['mid_level_staffs'] = mid_level_staffs
    resp['team'] = team
    resp['nurses_list'] = nurses_list
    resp['secretaries_list'] = secretaries_list
    resp['mid_level_staffs_list'] = mid_level_staffs_list
    resp['unassigned_patients'] = unassigned_patients_dict

    return ajax_response(resp)


@login_required
def assign_physician_member(request):

    success = False
    errors = []

    if request.method == 'POST':
        form = AssignPhysicianMemberForm(request.POST)

        if form.is_valid():
            user_id = form.cleaned_data['user_id']
            member_type = form.cleaned_data['member_type']
            physician_id = form.cleaned_data['physician_id']

            user = None
            user_profile = None
            physician = None
            physician_profile = None

            try:
                user = User.objects.get(id=user_id)
                user_profile = UserProfile.objects.get(
                    user=user, role=member_type)
            except User.DoesNotExist:
                errors.append('User does not exist.')
            except UserProfile.DoesNotExist:
                errors.append('%s profile does not exist' % member_type)

            try:
                physician = User.objects.get(id=physician_id)
                physician_profile = UserProfile.objects.get(
                    user=physician, role='physician')
            except User.DoesNotExist:
                errors.append('Physician doesnot exist.')
            except UserProfile.DoesNotExist:
                errors.append('Physician profile does not exist')

            if user_profile is not None and physician_profile is not None:
                if member_type == 'patient':
                    controller = PatientController(
                        patient=user,
                        physician=physician)
                    controller.save()
                else:
                    team_member = PhysicianTeam(
                        member=user,
                        physician=physician)
                    team_member.save()
                success = True

    resp = {}
    resp['success'] = success
    resp['errors'] = errors
    return ajax_response(resp)


@login_required
def unassign_physician_member(request):

    success = False
    errors = []

    if request.method == 'POST':
        # Unassign form fields are same as assign form
        form = AssignPhysicianMemberForm(request.POST)

        if form.is_valid():
            user_id = form.cleaned_data['user_id']
            member_type = form.cleaned_data['member_type']
            physician_id = form.cleaned_data['physician_id']

            user = None
            physician = None

            try:
                user = User.objects.get(id=user_id)
                physician = User.objects.get(id=physician_id)
            except User.DoesNotExist:
                errors.append('User does not exist!')

            if user is not None and physician is not None:

                if member_type == 'patient':
                    try:
                        controller = PatientController.objects.get(
                            patient=user, physician=physician)
                        controller.delete()
                        success = True
                    except PatientController.DoesNotExist:
                        errors.append('The patient was never assigned.')

                elif member_type in ['nurse', 'secretary', 'mid-level']:
                    try:
                        member = PhysicianTeam.objects.get(
                            physician=physician, member=user)
                        member.delete()
                        success = True
                    except PhysicianTeam.DoesNotExist:
                        errors.append('The staff was never assigned.')

        resp = {}
        resp['success'] = success
        resp['errors'] = errors

        return ajax_response(resp)


@login_required
def list_assigned_physicians(request):
    ''' Returns both assigned and unassigned_physicians '''
    success = False
    errors = []
    physicians_list = []
    unassigned_physicians_list = []
    if request.method == 'GET':
        user_id = request.GET.get('user_id')
        member_type = request.GET.get('member_type')

        if member_type in ['nurse', 'secretary', 'mid-level', 'patient']:
            user = None
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                errors.append('User doesnot exist')
            if user is not None:
                if member_type == 'patient':
                    controllers = PatientController.objects.filter(
                        patient=user)
                    physician_ids = [x.physician.id for x in controllers]
                else:
                    teams = PhysicianTeam.objects.filter(member=user)
                    physician_ids = [x.physician.id for x in teams]

                physicians = UserProfile.objects.filter(
                    user__id__in=physician_ids)
                physicians_list = UserProfileSerializer(
                    physicians, many=True).data

                unassigned_physicians = UserProfile.objects.filter(
                    role='physician').exclude(user__id__in=physician_ids)
                unassigned_physicians_list = UserProfileSerializer(
                    unassigned_physicians, many=True).data

                success = True

    resp = {}
    resp['success'] = success
    resp['errors'] = errors
    resp['physicians'] = physicians_list
    resp['unassigned_physicians'] = unassigned_physicians_list
    return ajax_response(resp)
