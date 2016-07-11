from datetime import datetime
from django.db.models import Max
from django.core.servers.basehttp import FileWrapper
from django.http import Http404, HttpResponse
from django.db.models import Q
from common.views import *

from emr.models import UserProfile, ToDo, ToDoComment, Label, ToDoAttachment, EncounterTodoRecord, \
    Encounter, TodoActivity, TaggedToDoOrder, LabeledToDoList, PhysicianTeam, PatientController, SharingPatient
from emr.operations import op_add_event, op_add_todo_event

from .serializers import TodoSerializer, ToDoCommentSerializer, SafeUserSerializer, \
    TodoActivitySerializer, LabelSerializer, LabeledToDoListSerializer
from encounters_app.serializers import EncounterSerializer
from users_app.serializers import UserProfileSerializer

from emr.manage_patient_permissions import check_permissions
from problems_app.operations import add_problem_activity
from .operations import add_todo_activity


def is_patient(user):
    try:
        profile = UserProfile.objects.get(user=user)
        return profile.role == 'patient'
    except UserProfile.DoesNotExist:
        return False

# set problem authentication to false if not physician, admin
def set_problem_authentication_false(request, todo):
    if todo.problem:
        problem = todo.problem
        
        actor_profile = UserProfile.objects.get(user=request.user)

        role = actor_profile.role

        if role in ['physician', 'admin']:
            authenticated = True
        else:
            authenticated = False

        problem.authenticated = authenticated
        problem.save()

@login_required
def get_todo_activity(request, todo_id, last_id):
    resp = {}
    resp['success'] = False

    try:
        todo = ToDo.objects.get(id=todo_id)
    except ToDo.DoesNotExist:
        raise Http404("ToDo DoesNotExist")

    activites = TodoActivity.objects.filter(todo=todo).filter(id__gt=last_id)
    activity_holder = TodoActivitySerializer(activites, many=True).data
    resp['activities'] = activity_holder
    resp['success'] = True

    return ajax_response(resp)


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
            due_date = datetime.strptime(due_date, '%m/%d/%Y').date()

        patient = User.objects.get(id=patient_id)
        physician = request.user

        new_todo = ToDo(patient=patient, todo=todo_name, due_date=due_date)
        order =  ToDo.objects.filter(patient=patient).aggregate(Max('order'))
        if not order['order__max']:
            order = 1
        else:
            order = order['order__max'] + 1
        new_todo.order = order
        new_todo.save()

        if new_todo.problem:
            problem_name = new_todo.problem.problem_name
        else:
            problem_name = ''
        summary = '''Added <u>todo</u> <a href="#/todo/%s"><b>%s</b></a> for <u>problem</u> <b>%s</b>''' % (new_todo.id, todo_name, problem_name)

        op_add_todo_event(physician, patient, summary, new_todo)

        # todo activity
        activity = '''
            Added this todo.
        '''
        add_todo_activity(new_todo, actor_profile, activity)

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

        summary = """Updated status of <u>todo</u> : <a href="#/todo/%s"><b>%s</b></a> ,<u>problem</u> <b>%s</b> to <b>%s</b>""" % (todo.id, todo.todo, problem_name, accomplished_label)

        op_add_todo_event(physician, patient, summary, todo)

        if todo.problem:
            add_problem_activity(todo.problem, actor_profile, summary, 'output')
            if accomplished:
                op_add_event(physician, patient, summary, todo.problem, True)

        # todo activity
        activity = '''
            Updated status of this todo to <b>%s</b>.
        ''' % (accomplished_label)
        add_todo_activity(todo, actor_profile, activity)

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

        # set problem authentication
        set_problem_authentication_false(request, todo)

    return ajax_response(resp)

@login_required
def update_order(request):
    resp = {}

    resp['success'] = False

    permissions = ['set_todo_order']

    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        datas = json.loads(request.body)
        id_todos = datas['todos']
        # patient's todo order
        if datas.has_key('patient_id'):
            patient_id = datas['patient_id']
            patient = User.objects.get(id=patient_id)

            todos = ToDo.objects.filter(id__in=id_todos).order_by('order')
            todos_order = []
            for todo in todos:
                todos_order.append(todo.order)

            key = 0
            for id in id_todos:
                todo = ToDo.objects.get(id=int(id))
                if not todos_order[key]:
                    order =  ToDo.objects.filter(patient=patient).aggregate(Max('order'))
                    if not order['order__max']:
                        order = 1
                    else:
                        order = order['order__max'] + 1
                    todo.order = order
                else:
                    todo.order = todos_order[key]
                todo.save()
                key = key + 1


            # set problem authentication
            set_problem_authentication_false(request, todo)

            # todo activity
            activity = '''
                Updated order of this todo.
            '''
            add_todo_activity(todo, actor_profile, activity)
        # tagged todo order
        if datas.has_key('tagged_user_id'):
            tagged_user_id = datas['tagged_user_id']
            user = User.objects.get(id=tagged_user_id)

            todos = TaggedToDoOrder.objects.filter(todo__id__in=id_todos).order_by('order')
            todos_order = []
            for todo in todos:
                todos_order.append(todo.order)

            key = 0
            for id in id_todos:
                todo = TaggedToDoOrder.objects.get(todo__id=int(id), user=user)
                if not todos_order[key]:
                    order =  TaggedToDoOrder.objects.filter(user=user).aggregate(Max('order'))
                    if not order['order__max']:
                        order = 1
                    else:
                        order = order['order__max'] + 1
                    todo.order = order
                else:
                    todo.order = todos_order[key]
                todo.save()
                key = key + 1
        # staff todo
        if datas.has_key('staff_id'):
            staff_id = datas['staff_id']
            user = User.objects.get(id=staff_id)

            todos = ToDo.objects.filter(id__in=id_todos).order_by('order')
            todos_order = []
            for todo in todos:
                todos_order.append(todo.order)

            key = 0
            for id in id_todos:
                todo = ToDo.objects.get(id=int(id))
                if not todos_order[key]:
                    order =  ToDo.objects.filter(user=user).aggregate(Max('order'))
                    if not order['order__max']:
                        order = 1
                    else:
                        order = order['order__max'] + 1
                    todo.order = order
                else:
                    todo.order = todos_order[key]
                todo.save()
                key = key + 1

            # todo activity
            activity = '''
                Updated order of this todo.
            '''
            add_todo_activity(todo, actor_profile, activity)

        # list todo
        if datas.has_key('list_id'):
            list_id = datas['list_id']
            labeled_list = LabeledToDoList.objects.get(id=int(list_id))
            labeled_list.todo_list = datas['todos']
            labeled_list.save()


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

    attachments = ToDoAttachment.objects.filter(todo=todo_info)
    attachment_todos_holder = []
    for attachment in attachments:
        attachment_dict = {
            'attachment': attachment.filename(),
            'datetime': datetime.strftime(attachment.datetime, '%Y-%m-%d'),
            'id': attachment.id,
            'user': SafeUserSerializer(attachment.user).data,
            'todo': TodoSerializer(attachment.todo).data,
        }
        attachment_todos_holder.append(attachment_dict)

    encounter_records = EncounterTodoRecord.objects.filter(
        todo=todo_info)
    encounter_ids = [long(x.encounter.id) for x in encounter_records]

    related_encounters = Encounter.objects.filter(id__in=encounter_ids)

    related_encounter_holder = EncounterSerializer(
        related_encounters, many=True).data

    activites = TodoActivity.objects.filter(todo=todo_info)
    activity_holder = TodoActivitySerializer(activites, many=True).data

    sharing_patients = SharingPatient.objects.filter(shared=todo_info.patient).order_by('sharing__first_name', 'sharing__last_name')

    sharing_patients_list = []
    for sharing_patient in sharing_patients:
        user_dict = UserProfileSerializer(sharing_patient.sharing.profile).data
        user_dict['problems'] = [x.id for x in sharing_patient.problems.all()]
        sharing_patients_list.append(user_dict)

    resp = {}
    resp['success'] = True
    resp['info'] = todo_dict
    resp['comments'] = comment_todos_holder
    resp['attachments'] = attachment_todos_holder
    resp['related_encounters'] = related_encounter_holder
    resp['activities'] = activity_holder
    resp['sharing_patients'] = sharing_patients_list

    return ajax_response(resp)

@login_required
def add_todo_comment(request, todo_id):
    resp = {}
    resp['success'] = False

    permissions = ['add_todo_comment']
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

    permissions = ['add_todo_comment']
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

    permissions = ['delete_todo_comment']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:

        todo_comment = ToDoComment.objects.get(id=comment_id)
        todo_comment.delete()

        resp['success'] = True

    return ajax_response(resp)

@login_required
def change_todo_text(request, todo_id):
    resp = {}
    resp['success'] = False

    permissions = ['add_todo']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:

        todo_text = request.POST.get('todo')

        todo = ToDo.objects.get(id=todo_id)
        todo.todo = todo_text
        todo.save()

        # set problem authentication
        set_problem_authentication_false(request, todo)

        resp['success'] = True

    return ajax_response(resp)

@login_required
def change_todo_due_date(request, todo_id):
    resp = {}
    resp['success'] = False

    permissions = ['add_todo']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:

        due_date = request.POST.get('due_date')
        if due_date and due_date != '':
            try:
                due_date = datetime.strptime(due_date, '%m/%d/%Y').date()
            except:
                resp['success'] = False
                todo = ToDo.objects.get(id=todo_id)
                todo_dict = TodoSerializer(todo).data
                resp['todo'] = todo_dict
                return ajax_response(resp)
        else:
            due_date = None

        todo = ToDo.objects.get(id=todo_id)
        todo.due_date = due_date
        todo.save()

        # set problem authentication
        set_problem_authentication_false(request, todo)

        # todo activity
        if due_date:
            activity = '''
                Changed due date of this todo to <b>%s</b>.
            ''' % (request.POST.get('due_date'))
        else:
             activity = '''
                Removed due date of this todo.
            '''
        add_todo_activity(todo, actor_profile, activity)

        resp['success'] = True

    return ajax_response(resp)

@login_required
def add_todo_label(request, label_id, todo_id):
    resp = {}
    resp['success'] = False

    permissions = ['add_todo']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:

        todo = ToDo.objects.get(id=todo_id)
        
        label = Label.objects.get(id=label_id)
        todo.labels.add(label)

        # set problem authentication
        set_problem_authentication_false(request, todo)

        resp['success'] = True

    return ajax_response(resp)


@login_required
def remove_todo_label(request, label_id, todo_id):
    resp = {}
    resp['success'] = False

    permissions = ['add_todo']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        label = Label.objects.get(id=label_id)
        todo = ToDo.objects.get(id=todo_id)
        todo.labels.remove(label)
        # set problem authentication
        set_problem_authentication_false(request, todo)

        resp['success'] = True

    return ajax_response(resp)

@login_required
def new_todo_label(request, todo_id):
    resp = {}
    resp['success'] = False
    resp['status'] = False
    resp['new_status'] = False

    permissions = ['add_todo']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        name = request.POST.get('name')
        css_class = request.POST.get('css_class')
        is_all = request.POST.get('is_all', False)
        if is_all:
            is_all = True
        else:
            is_all = False

        todo = ToDo.objects.get(id=todo_id)
        label = Label.objects.filter(name=name, css_class=css_class)
        if not label:
            label = Label(name=name, css_class=css_class)
            label.author = request.user
            label.is_all = is_all
            label.save()
            resp['new_status'] = True
            resp['new_label'] = LabelSerializer(label).data
        else:
            label = label[0]

        if (label.is_all == True) or ((label.is_all == False) and (label.author == request.user)):
            if not label in todo.labels.all():
                todo.labels.add(label)
                resp['status'] = True
                resp['label'] = LabelSerializer(label).data

        # set problem authentication
        set_problem_authentication_false(request, todo)

        resp['success'] = True

    return ajax_response(resp)

@login_required
def save_edit_label(request, label_id):
    resp = {}
    resp['success'] = False
    resp['status'] = False

    permissions = ['add_todo']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        name = request.POST.get('name')
        css_class = request.POST.get('css_class')

        label = Label.objects.get(id=label_id)

        if not Label.objects.filter(name=name, css_class=css_class):
            label.name = name
            label.css_class = css_class
            label.save()
            resp['status'] = True

        resp['label'] = LabelSerializer(label).data

        resp['success'] = True

    return ajax_response(resp)

@login_required
def delete_label(request, label_id):
    resp = {}
    resp['success'] = False

    permissions = ['add_todo']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:

        label = Label.objects.get(id=label_id)
        label.delete()

        resp['success'] = True

    return ajax_response(resp)

@login_required
def todo_access_encounter(request, todo_id):
    resp = {}
    todo = ToDo.objects.get(id=todo_id)
    physician = request.user
    patient = todo.patient

    if todo.problem:
        summary = '''<a href="#/todo/%s"><b>%s</b></a> for <b>%s</b> was visited.''' % (todo.id, todo.todo, todo.problem.problem_name)
    else:
        summary = '''<a href="#/todo/%s"><b>%s</b></a> was visited.''' % (todo.id, todo.todo)

    op_add_todo_event(physician, patient, summary, todo)
    if todo.problem:
        op_add_event(physician, patient, summary, todo.problem, True)

    return ajax_response(resp)

@login_required
def add_todo_attachment(request, todo_id):
    resp = {}
    resp['success'] = False

    permissions = ['add_todo']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        if request.method == 'POST':
            todo = ToDo.objects.get(id=todo_id)

            attachment = ToDoAttachment(todo=todo, user=request.user, attachment=request.FILES['0'])
            attachment.save()

            resp['success'] = True

            attachment_dict = {
                'attachment': attachment.filename(),
                'datetime': datetime.strftime(attachment.datetime, '%Y-%m-%d'),
                'id': attachment.id,
                'user': SafeUserSerializer(attachment.user).data,
                'todo': TodoSerializer(attachment.todo).data,
            }
            resp['attachment'] = attachment_dict

            # todo activity
            activity = '''
                Attached <b>%s</b> to this todo.
            ''' % (attachment.filename())
            add_todo_activity(todo, actor_profile, activity, comment=None, attachment=attachment)


    return ajax_response(resp)

def download_attachment(request, attachment_id):
    """
    Create a file to download.
    """
    attachment = ToDoAttachment.objects.get(id=attachment_id)
    wrapper = FileWrapper(attachment.attachment)
    response = HttpResponse(wrapper, content_type='application/%s' % attachment.file_extension_lower())

    filename = '{}.{}'.format(attachment.filename(), attachment.file_extension_lower())
    response['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    return response

@login_required
def delete_attachment(request, attachment_id):
    resp = {}
    resp['success'] = False
    permissions = ['add_todo']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        attachment = ToDoAttachment.objects.get(id=attachment_id)
        # todo activity
        activity = '''
            Deleted <b>%s</b> from this todo.
        ''' % (attachment.filename())
        add_todo_activity(attachment.todo, actor_profile, activity)

        attachment.delete()

        resp['success'] = True

    return ajax_response(resp)

@login_required
def add_todo_member(request, todo_id):
    resp = {}
    resp['success'] = False

    permissions = ['add_todo']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:

        member_id = request.POST.get('id')
        todo = ToDo.objects.get(id=todo_id)
        member = UserProfile.objects.get(id=int(member_id))
        todo.members.add(member)

        tagged_todo = TaggedToDoOrder(todo=todo, user=member.user)
        tagged_todo.save()

        # set problem authentication
        set_problem_authentication_false(request, todo)

        # todo activity
        activity = '''
            <b>%s %s - %s</b> joined this todo.
        ''' % (member.user.first_name, member.user.last_name, member.role)
        add_todo_activity(todo, actor_profile, activity)

        resp['success'] = True

    return ajax_response(resp)


@login_required
def remove_todo_member(request, todo_id):
    resp = {}
    resp['success'] = False

    permissions = ['add_todo']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        member_id = request.POST.get('id')
        todo = ToDo.objects.get(id=todo_id)
        member = UserProfile.objects.get(id=int(member_id))
        todo.members.remove(member)

        if TaggedToDoOrder.objects.filter(todo=todo, user=member.user):
            tagged_todo = TaggedToDoOrder.objects.get(todo=todo, user=member.user)
            tagged_todo.delete()

        # set problem authentication
        set_problem_authentication_false(request, todo)

        # todo activity
        activity = '''
            <b>%s %s - %s</b> left this todo.
        ''' % (member.user.first_name, member.user.last_name, member.role)
        add_todo_activity(todo, actor_profile, activity)

        resp['success'] = True

    return ajax_response(resp)

@login_required
def get_labels(request, user_id):

    user = User.objects.get(id=user_id)
    labels = Label.objects.filter(Q(is_all=True) | Q(Q(is_all=False) & Q(author=user)))

    labels_holder = []
    for label in labels:
        label_dict = LabelSerializer(label).data
        labels_holder.append(label_dict)

    resp = {}
    resp['labels'] = labels_holder

    return ajax_response(resp)

@login_required
def get_user_todos(request, user_id):
    user = User.objects.get(id=user_id)
    todos = TaggedToDoOrder.objects.filter(user=user).order_by('order', 'todo__due_date')

    todos_holder = []
    for todo in todos:
        todo_dict = TodoSerializer(todo.todo).data
        todos_holder.append(todo_dict)

    resp = {}
    resp['tagged_todos'] = todos_holder

    todos = ToDo.objects.filter(user=user).order_by('order', 'due_date')
    todos_holder = []
    for todo in todos:
        todo_dict = TodoSerializer(todo).data
        todos_holder.append(todo_dict)
    resp['personal_todos'] = todos_holder

    return ajax_response(resp)

@login_required
def add_staff_todo(request, user_id):
    resp = {}
    resp['success'] = False

    permissions = ['add_todo']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:

        todo_name = request.POST.get('name')
        due_date = request.POST.get('due_date', None)
        if due_date:
            due_date = datetime.strptime(due_date, '%m/%d/%Y').date()

        user = User.objects.get(id=user_id)

        new_todo = ToDo(user=user, todo=todo_name, due_date=due_date)
        order =  ToDo.objects.filter(user=user).aggregate(Max('order'))
        if not order['order__max']:
            order = 1
        else:
            order = order['order__max'] + 1
        new_todo.order = order
        new_todo.save()

        # todo activity
        activity = '''
            Added this todo.
        '''
        add_todo_activity(new_todo, actor_profile, activity)

        new_todo_dict = TodoSerializer(new_todo).data
        resp['todo'] = new_todo_dict
        resp['success'] = True

    return ajax_response(resp)

@login_required
def add_staff_todo_list(request, user_id):
    resp = {}
    resp['success'] = False

    permissions = ['add_todo']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:

        datas = json.loads(request.body)
        list_name = datas['name']
        labels = datas['labels']
        user = User.objects.get(id=user_id)

        new_list = LabeledToDoList(user=user, name=list_name)
        new_list.save()

        label_ids = []
        for label in labels:
            l = Label.objects.get(id=label['id'])
            new_list.labels.add(l)
            label_ids.append(l.id)


        new_list_dict = LabeledToDoListSerializer(new_list).data

        todos = ToDo.objects.filter(labels__id__in=label_ids).distinct().order_by('due_date')
        todos_holder = []
        for todo in todos:
            todo_dict = TodoSerializer(todo).data
            todos_holder.append(todo_dict)

        new_list_dict['todos'] = todos_holder
        new_list_dict['expanded'] = new_list.expanded

        resp['new_list'] = new_list_dict
        resp['success'] = True

    return ajax_response(resp)

@login_required
def get_user_label_lists(request, user_id):
    resp = {}
    user = User.objects.get(id=user_id)
    lists = LabeledToDoList.objects.filter(user=user)
    lists_holder = []
    for label_list in lists:
        list_dict = LabeledToDoListSerializer(label_list).data
        label_ids = []
        for label in label_list.labels.all():
            label_ids.append(label.id)

        if label_list.todo_list:
            todos_qs = ToDo.objects.filter(labels__id__in=label_ids).distinct()
            todos = []
            for id in label_list.todo_list:
                if todos_qs.filter(id=id):
                    todos.append(todos_qs.get(id=id))
            for todo in todos_qs:
                if not todo in todos:
                    todos.append(todo)

        else:
            todos = ToDo.objects.filter(labels__id__in=label_ids).distinct().order_by('due_date')
        todos_holder = []
        for todo in todos:
            todo_dict = TodoSerializer(todo).data
            todos_holder.append(todo_dict)

        list_dict['todos'] = todos_holder
        list_dict['expanded'] = label_list.expanded
        lists_holder.append(list_dict)
        
    resp['todo_lists'] = lists_holder

    return ajax_response(resp)

@login_required
def delete_todo_list(request, list_id):
    resp = {}
    resp['success'] = False
    permissions = ['add_todo']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        todo_list = LabeledToDoList.objects.get(id=list_id)

        todo_list.delete()

        resp['success'] = True

    return ajax_response(resp)

@login_required
def staff_all_todos(request, user_id):
    resp = {}
    staff = User.objects.get(id=user_id)

    team_members = PhysicianTeam.objects.filter(member=staff)
    physician_ids = [long(x.physician.id) for x in team_members]
    patient_controllers = PatientController.objects.filter(physician__id__in=physician_ids)
    patient_ids = [long(x.patient.id) for x in patient_controllers]

    todos = ToDo.objects.filter(accomplished=False, patient__id__in=patient_ids, due_date__lte=datetime.now()).order_by('-due_date')
    todos_list = TodoSerializer(todos, many=True).data

    resp['all_todos_list'] = todos_list

    return ajax_response(resp)

@login_required
def open_todo_list(request, list_id):
    resp = {}
    resp['success'] = False
    permissions = ['add_todo']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        todo_list = LabeledToDoList.objects.get(id=list_id)
        expanded = todo_list.expanded
        datas = json.loads(request.body)
        todos = datas['todos']

        for todo in todos:
            if not todo['id'] in expanded:
                expanded.append(todo['id'])

        todo_list.expanded = expanded
        todo_list.save()

        resp['success'] = True

    return ajax_response(resp)