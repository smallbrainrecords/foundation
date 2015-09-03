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
    ('add_problem', 'Add Problem'),
    ('modify_problem', 'Modify Problem'),
    ('add_problem_image', 'Add Problem Image'),
    ('set_problem_authenticated', 'Set Problem Authentication Status'),
    ('set_problem_controlled', 'Set Problem Controlled Status'),
    ('set_problem_active', 'Set Problem Active Status'),
    ('add_problem_note', 'Add Problem Note'),
    # Goal
    ('add_goal', 'Add Goal'),
    ('modify_goal', 'Modify Goal'),
    # Todo
    ('add_todo', 'Add Todo'),
    ('set_todo_status', 'Set Todo Status'),
    # Patient Profile
    ('update_patient_profile', 'Update Patient Profile'),
    # Encounter
    ('add_encounter', 'Add Encounter'),
    ('add_encounter_event', 'Add Encounter Event'), ]


ROLE_PERMISSIONS = {}

ROLE_PERMISSIONS['admin'] = GLOBAL_PERMISSIONS


ROLE_PERMISSIONS['patient'] = [
    # Problem
    ('add_problem', 'Add Problem'),
    ('modify_problem', 'Modify Problem'),
    ('add_problem_image', 'Add Problem Image'),
    ('add_problem_note', 'Add Problem Note'),
    # Goal
    ('add_goal', 'Add Goal'),
    ('modify_goal', 'Modify Goal'),
    # Todo
    ('add_todo', 'Add Todo'),
    ('set_todo_status', 'Set Todo Status'),
    # Patient Profile
    ('update_patient_profile', 'Update Patient Profile'), ]


ROLE_PERMISSIONS['physician'] = [
    # Problem
    ('add_problem', 'Add Problem'),
    ('modify_problem', 'Modify Problem'),
    ('add_problem_image', 'Add Problem Image'),
    ('set_problem_authenticated', 'Set Problem Authentication Status'),
    ('set_problem_controlled', 'Set Problem Controlled Status'),
    ('set_problem_active', 'Set Problem Active Status'),
    ('add_problem_note', 'Add Problem Note'),
    # Goal
    ('add_goal', 'Add Goal'),
    ('modify_goal', 'Modify Goal'),
    # Todo
    ('add_todo', 'Add Todo'),
    ('set_todo_status', 'Set Todo Status'),
    # Patient Profile
    ('update_patient_profile', 'Update Patient Profile'),
    # Encounter
    ('add_encounter', 'Add Encounter'),
    ('add_encounter_event', 'Add Encounter Event'), ]

ROLE_PERMISSIONS['mid-level'] = [
    # Problem
    ('add_problem', 'Add Problem'),
    ('modify_problem', 'Modify Problem'),
    ('add_problem_image', 'Add Problem Image'),
    ('set_problem_authenticated', 'Set Problem Authentication Status'),
    ('set_problem_controlled', 'Set Problem Controlled Status'),
    ('set_problem_active', 'Set Problem Active Status'),
    ('add_problem_note', 'Add Problem Note'),
    # Goal
    ('add_goal', 'Add Goal'),
    ('modify_goal', 'Modify Goal'),
    # Todo
    ('add_todo', 'Add Todo'),
    ('set_todo_status', 'Set Todo Status'),
    # Patient Profile
    ('update_patient_profile', 'Update Patient Profile'),
    # Encounter
    ('add_encounter', 'Add Encounter'),
    ('add_encounter_event', 'Add Encounter Event'), ]


ROLE_PERMISSIONS['nurse'] = [
    # Problem
    ('add_problem', 'Add Problem'),
    ('modify_problem', 'Modify Problem'),
    ('add_problem_image', 'Add Problem Image'),
    ('add_problem_note', 'Add Problem Note'),
    # Goal
    ('add_goal', 'Add Goal'),
    ('modify_goal', 'Modify Goal'),
    # Todo
    ('add_todo', 'Add Todo'),
    ('set_todo_status', 'Set Todo Status'),
    # Patient Profile
    ('update_patient_profile', 'Update Patient Profile'), ]


ROLE_PERMISSIONS['secretary'] = [
    # Todo
    ('add_todo', 'Add Todo'),
    ('set_todo_status', 'Set Todo Status'),
    # Patient Profile
    ('update_patient_profile', 'Update Patient Profile'), ]


def contains(list1, list2):
    for item in list1:
        if item not in list2:
            return False
    return True


def check_permissions(permission, actor):
    try:
        actor_profile = UserProfile.objects.get(user=actor)
    except:
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
