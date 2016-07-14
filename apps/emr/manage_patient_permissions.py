'''
    PERMISSIONS for managing patient
'''
from .models import UserProfile, SharingPatient
from .models import PatientController, PhysicianTeam
import logging


ROLES = (
    ('patient', 'Patient'),
    ('physician', 'Physician'),
    ('mid-level', 'Mid Level PA/NP'),
    ('nurse', 'Nurse'),
    ('secretary', 'Secretary'),
    ('admin', 'Admin'),)

GLOBAL_PERMISSIONS = [
    # Problem
    'add_problem',
    'modify_problem',
    'add_problem_image',
    'delete_problem_image',
    'set_problem_authenticated',
    'set_problem_controlled',
    'set_problem_active',
    'relate_problem',
    'set_problem_order',
    'change_problem_name',
    'add_problem_label',
    # Problem Notes
    'add_patient_problem_note',
    'add_physician_problem_note',
    'add_nurse_problem_note',
    # Goal
    'add_goal', 'Add Goal',
    'modify_goal', 'Modify Goal',
    # Todo
    'add_todo',
    'set_todo_status',
    'set_todo_order',
    'add_todo_comment',
    'delete_todo_comment',
    # Patient Profile
    'update_patient_profile',
    # Encounter
    'add_encounter',
    'add_encounter_event',
    'add_encounter_timestamp',
    # observation
    'add_observation',
    'add_observation_note',
    'edit_observation_note',
    'delete_observation_note',
    'delete_observation_component',
    'edit_observation_component',
    # sharing
    'add_sharing_patient',
    'remove_sharing_patient',
    # Pain
    'update_pain', ]


ROLE_PERMISSIONS = {}

ROLE_PERMISSIONS['admin'] = GLOBAL_PERMISSIONS


ROLE_PERMISSIONS['patient'] = [
    # Problem
    'add_problem',
    'modify_problem',
    'add_problem_image',
    'add_patient_problem_note',
    'set_problem_controlled',
    'set_problem_active',
    'relate_problem',
    'set_problem_order',
    'change_problem_name',
    'add_problem_label',
    # Goal
    'add_goal',
    'modify_goal',
    # Todo
    'add_todo',
    'set_todo_status',
    'set_todo_order',
    'add_todo_comment',
    # Patient Profile
    'update_patient_profile',
    # encounter
    'add_encounter_timestamp',
    # observation
    'add_observation',
    'add_observation_note',
    'remove_sharing_patient',
    # Pain
    'update_pain', ]


ROLE_PERMISSIONS['physician'] = [
    # Problem
    'add_problem',
    'modify_problem',
    'add_problem_image',
    'delete_problem_image',
    'set_problem_authenticated',
    'set_problem_controlled',
    'set_problem_active',
    'add_physician_problem_note',
    'relate_problem',
    'set_problem_order',
    'change_problem_name',
    'add_problem_label',
    'add_common_problem_list',
    # Goal
    'add_goal',
    'modify_goal',
    # Todo
    'add_todo',
    'set_todo_status',
    'set_todo_order',
    'add_todo_comment',
    'delete_todo_comment',
    # Patient Profile
    'update_patient_profile',
    # Encounter
    'add_encounter',
    'add_encounter_event',
    'add_encounter_timestamp',
    # observation
    'add_observation',
    'add_observation_note',
    'edit_observation_note',
    'delete_observation_note',
    'delete_observation_component',
    'edit_observation_component',
    # sharing
    'add_sharing_patient',
    'remove_sharing_patient',
    # Pain
    'update_pain', ]

ROLE_PERMISSIONS['mid-level'] = [
    # Problem
    'add_problem',
    'modify_problem',
    'add_problem_image',
    'delete_problem_image',
    'set_problem_controlled',
    'set_problem_active',
    'add_physician_problem_note',
    'relate_problem',
    'set_problem_order',
    'change_problem_name',
    'add_problem_label',
    'add_common_problem_list',
    # Goal
    'add_goal',
    'modify_goal',
    # Todo
    'add_todo',
    'set_todo_status',
    'set_todo_order',
    'add_todo_comment',
    # Patient Profile
    'update_patient_profile',
    # Encounter
    'add_encounter',
    'add_encounter_event',
    'add_encounter_timestamp',
    # observation
    'add_observation',
    'add_observation_note',
    # sharing
    'add_sharing_patient',
    'remove_sharing_patient',
    # Pain
    'update_pain', ]


ROLE_PERMISSIONS['nurse'] = [
    # Problem
    'add_problem',
    'modify_problem',
    'add_problem_image',
    'add_nurse_problem_note',
    'change_problem_name',
    'add_problem_label',
    # Goal
    'add_goal',
    'modify_goal',
    # Todo
    'add_todo',
    'set_todo_status',
    'set_todo_order',
    'add_todo_comment',
    # Patient Profile
    'update_patient_profile',
    # encounter
    'add_encounter_timestamp',
    # observation
    'add_observation',
    'add_observation_note',
    # sharing
    'add_sharing_patient',
    'remove_sharing_patient',
    # Pain
    'update_pain', ]


ROLE_PERMISSIONS['secretary'] = [
    # Problem
    'add_problem_label',
    # Todo
    'add_todo',
    'set_todo_status',
    'set_todo_order',
    'add_todo_comment',
    # encounter
    'add_encounter_timestamp',
    # observation
    'add_observation',
    'add_observation_note',
    # sharing
    'add_sharing_patient',
    'remove_sharing_patient',
    # Patient Profile
    'update_patient_profile', ]


def contains(list1, list2):

    if len(list1) < 1:
        return False

    for item in list1:
        if item not in list2:
            return False
    return True


def check_permissions(permission, actor):
    try:
        actor_profile = UserProfile.objects.get(user=actor)
    except UserProfile.DoesNotExist:
        actor_profile = None

    permitted = False

    if actor_profile is not None:
        user_permissions = ROLE_PERMISSIONS[actor_profile.role]
        if contains(permission, user_permissions):
            permitted = True

    return actor_profile, permitted


def check_access(patient, actor_profile):
    '''
        Buggy - Fix IT
    '''

    allowed = False

    if actor_profile.role == 'physician':
        is_controller = PatientController.objects.filter(
            patient=patient, physician=actor_profile.user).exists()
        allowed = is_controller
    elif actor_profile.role == 'patient':
        if patient.id == actor_profile.user.id:
            allowed = True
        else:
            is_sharing = SharingPatient.objects.filter(sharing=actor_profile.user, shared=patient).exists()
            allowed = is_sharing
    elif actor_profile.role == 'admin':
        allowed = True
    else:
        controllers = PatientController.objects.filter(
            patient=patient)
        physician_ids = [x.physician.id for x in controllers]
        is_staff = PhysicianTeam.objects.filter(
            physician__id__in=physician_ids).exists()

        logging.error(is_staff)

        allowed = is_staff

    return allowed


def sample_view(request):
    '''
    permission = ['permission_1', 'permission_2']
    actor = request.user

    actor_profile, permitted = check_permissions(permission, actor)

    if permitted:
        logging.error('do action')
    else:
        logging.error('show error message')
    '''
    pass
