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
'''
    PERMISSIONS for managing patient
'''
import logging

from .models import PatientController, PhysicianTeam
from .models import UserProfile, SharingPatient

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
    'delete_problem',
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
    'delete_encounter',
    # a1c
    'add_a1c',
    'add_a1c_note',
    'edit_a1c_note',
    'delete_a1c_note',
    'delete_observation_component',
    'edit_observation_component',
    # sharing
    'add_sharing_patient',
    'remove_sharing_patient',
    # my story
    'add_my_story_tab',
    'save_text_component',
    # data
    'add_data_type',
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
    # a1c
    'add_a1c',
    'add_a1c_note',
    'delete_observation_component',
    'edit_observation_component',
    'remove_sharing_patient',
    # my story
    'add_my_story_tab',
    'save_text_component',
    # data
    'set_data_order',
    'add_data_type',
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
    'delete_problem',
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
    'delete_encounter',
    # a1c
    'add_a1c',
    'add_a1c_note',
    'edit_a1c_note',
    'delete_a1c_note',
    'delete_observation_component',
    'edit_observation_component',
    # sharing
    'add_sharing_patient',
    'remove_sharing_patient',
    # my story
    'add_my_story_tab',
    'save_text_component',
    # data
    'set_data_order',
    'add_data_type',
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
    'delete_problem',
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
    # a1c
    'add_a1c',
    'add_a1c_note',
    # sharing
    'add_sharing_patient',
    'remove_sharing_patient',
    # my story
    'save_text_component',
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
    # a1c
    'add_a1c',
    'add_a1c_note',
    # sharing
    'add_sharing_patient',
    'remove_sharing_patient',
    # my story
    'save_text_component',
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
    # a1c
    'add_a1c',
    'add_a1c_note',
    # sharing
    'add_sharing_patient',
    'remove_sharing_patient',
    # my story
    'save_text_component',
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
