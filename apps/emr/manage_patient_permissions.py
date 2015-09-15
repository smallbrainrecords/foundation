'''
    PERMISSIONS for managing patient
'''
from .models import UserProfile


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
    # Patient Profile
    'update_patient_profile',
    # Encounter
    'add_encounter',
    'add_encounter_event',
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
    # Goal
    'add_goal',
    'modify_goal',
    # Todo
    'add_todo',
    'set_todo_status',
    # Patient Profile
    'update_patient_profile',
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
    # Goal
    'add_goal',
    'modify_goal',
    # Todo
    'add_todo',
    'set_todo_status',
    # Patient Profile
    'update_patient_profile',
    # Encounter
    'add_encounter',
    'add_encounter_event',
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
    # Goal
    'add_goal',
    'modify_goal',
    # Todo
    'add_todo',
    'set_todo_status',
    # Patient Profile
    'update_patient_profile',
    # Encounter
    'add_encounter',
    'add_encounter_event',
    # Pain
    'update_pain', ]


ROLE_PERMISSIONS['nurse'] = [
    # Problem
    'add_problem',
    'modify_problem',
    'add_problem_image',
    'add_nurse_problem_note',
    # Goal
    'add_goal',
    'modify_goal',
    # Todo
    'add_todo',
    'set_todo_status',
    # Patient Profile
    'update_patient_profile',
    # Pain
    'update_pain', ]


ROLE_PERMISSIONS['secretary'] = [
    # Todo
    'add_todo',
    'set_todo_status',
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