from datetime import datetime
from django.db.models import Max
from common.views import *

from emr.models import UserProfile, ToDo, ToDoComment
from emr.operations import op_add_event

from .serializers import TodoSerializer, ToDoCommentSerializer

from emr.manage_patient_permissions import check_permissions
from problems_app.operations import add_problem_activity


def is_patient(user):
    try:
        profile = UserProfile.objects.get(user=user)
        return profile.role == 'patient'
    except UserProfile.DoesNotExist:
        return False


# Todos
@login_required
def add_patient_todo(request, patient_id):

    resp = {}
    resp['success'] = False

    permissions = ['add_todo']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:

        todo_name = request.POST.get('name')
        due_date = request.POST.get('due_date', None)
        if due_date:
            due_date = datetime.strptime(due_date, '%Y-%m-%d').date()

        patient = User.objects.get(id=patient_id)
        physician = request.user

        new_todo = ToDo(patient=patient, todo=todo_name, due_date=due_date)
        order =  ToDo.objects.all().aggregate(Max('order'))
        if not order['order__max']:
            order = 1
        else:
            order = order['order__max'] + 1
        new_todo.order = order
        new_todo.save()

        if new_todo.problem:
            problem_name = todo.problem.problem_name
        else:
            problem_name = ''
        summary = '''
            Added <u>todo</u> <a href="#/todo/%s"><b>%s</b></a> for <u>problem</u> <b>%s</b>
            ''' % (new_todo.id, todo_name, problem_name)

        op_add_event(physician, patient, summary)

        new_todo_dict = TodoSerializer(new_todo).data
        resp['todo'] = new_todo_dict
        resp['success'] = True

    return ajax_response(resp)


@login_required
def update_todo_status(request, todo_id):

    resp = {}
    resp['success'] = False
    permissions = ['set_todo_status']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if request.method == 'POST' and permitted:

        todo = ToDo.objects.get(id=todo_id)
        accomplished = request.POST.get('accomplished') == 'true'
        todo.accomplished = accomplished
        todo.save()

        physician = request.user
        patient = todo.patient

        if todo.problem:
            problem_name = todo.problem.problem_name
        else:
            problem_name = ''

        if accomplished:
            accomplished_label = 'accomplished'
        else:
            accomplished_label = 'not accomplished'

        summary = """
            Updated status of <u>todo</u> : <a href="#/todo/%s"><b>%s</b></a> ,
            <u>problem</u> <b>%s</b> to <b>%s</b>
            """ % (todo.id, todo.todo, problem_name, accomplished_label)

        op_add_event(physician, patient, summary, todo.problem)

        if todo.problem:
            add_problem_activity(todo.problem, actor_profile, summary)

        resp['success'] = True
         # Accomplished Todos
        accomplished_todos = ToDo.objects.filter(
            patient=patient, accomplished=True)
        accomplished_todo_list = []
        for todo in accomplished_todos:
            todo_dict = TodoSerializer(todo).data
            accomplished_todo_list.append(todo_dict)
        resp['accomplished_todos'] = accomplished_todo_list

        # Not accomplished Todos
        pending_todos = ToDo.objects.filter(
            patient=patient, accomplished=False)
        pending_todo_list = []
        for todo in pending_todos:
            todo_dict = TodoSerializer(todo).data
            pending_todo_list.append(todo_dict)
        resp['pending_todos'] = pending_todo_list

    return ajax_response(resp)

@login_required
def update_order(request):
    resp = {}

    resp['success'] = False

    permissions = ['modify_problem']

    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        id_todos = json.loads(request.body)['todos']
        todos = ToDo.objects.filter(id__in=id_todos).order_by('order')
        todos_order = []
        for todo in todos:
            todos_order.append(todo.order)

        key = 0
        for id in id_todos:
            todo = ToDo.objects.get(id=int(id))
            if not todos_order[key]:
                order =  ToDo.objects.all().aggregate(Max('order'))
                if not order['order__max']:
                    order = 1
                else:
                    order = order['order__max'] + 1
                todo.order = order
            else:
                todo.order = todos_order[key]
            todo.save()
            key = key + 1

        resp['success'] = True
    return ajax_response(resp)

@login_required
def get_todo_info(request, todo_id):
    todo_info = ToDo.objects.get(id=todo_id)
    todo_dict = TodoSerializer(todo_info).data

    comments = ToDoComment.objects.filter(todo=todo_info)
    comment_todos_holder = []
    for comment in comments:
        comment_dict = ToDoCommentSerializer(comment).data
        comment_todos_holder.append(comment_dict)

    resp = {}
    resp['success'] = True
    resp['info'] = todo_dict
    resp['comments'] = comment_todos_holder

    return ajax_response(resp)

@login_required
def add_todo_comment(request, todo_id):
    resp = {}
    resp['success'] = False

    permissions = ['add_todo']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:

        comment = request.POST.get('comment')

        todo = ToDo.objects.get(id=todo_id)
        user = request.user

        todo_comment = ToDoComment(todo=todo, user=user, comment=comment)
        todo_comment.save()

        todo_comment_dict = ToDoCommentSerializer(todo_comment).data
        resp['comment'] = todo_comment_dict
        resp['success'] = True

    return ajax_response(resp)

@login_required
def edit_todo_comment(request, comment_id):
    resp = {}
    resp['success'] = False

    permissions = ['add_todo']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        comment = request.POST.get('comment')

        todo_comment = ToDoComment.objects.get(id=comment_id)
        todo_comment.comment = comment
        todo_comment.save()

        todo_comment_dict = ToDoCommentSerializer(todo_comment).data
        resp['comment'] = todo_comment_dict
        resp['success'] = True

    return ajax_response(resp)

@login_required
def delete_todo_comment(request, comment_id):
    resp = {}
    resp['success'] = False

    permissions = ['add_todo']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:

        todo_comment = ToDoComment.objects.get(id=comment_id)
        todo_comment.delete()

        resp['success'] = True

    return ajax_response(resp)
