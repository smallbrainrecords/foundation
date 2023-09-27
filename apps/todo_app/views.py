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

import logging
from collections import OrderedDict
from wsgiref.util import FileWrapper

from common.views import *
from dateutil import parser
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import connection
from django.db.models import Max, Q
from document_app.serializers import *
from emr.models import (
    Encounter,
    EncounterTodoRecord,
    Label,
    LabeledToDoList,
    PatientController,
    PhysicianTeam,
    SharingPatient,
    TaggedToDoOrder,
    ToDo,
    ToDoAttachment,
    ToDoComment,
)
from emr.operations import op_add_event, op_add_todo_event
from problems_app.operations import add_problem_activity
from rest_framework.decorators import api_view
from todo_app.operations import *
from users_app.serializers import SafeUserSerializer, UserProfileSerializer

from apps.todo_app import todo_list

from .serializers import (
    LabeledToDoListSerializer,
    TodoActivitySerializer,
    ToDoCommentSerializer,
)


@login_required
#@timeit
def get_todo_activity(request, todo_id, last_id):
    activities = TodoActivity.objects.filter(todo_id=todo_id).filter(id__gt=last_id)
    resp = {'activities': TodoActivitySerializer(activities, many=True).data, 'success': True}
    return ajax_response(resp)


@permissions_required(["add_todo"])
@login_required
#@timeit
def add_patient_todo(request, patient_id):
    # Get post params
    todo_name = request.POST.get('name')
    due_date = request.POST.get('due_date', None)
    if due_date:
        due_date = parser.parse(due_date, dayfirst=False, ignoretz=True)
    members = request.POST.getlist('members[]', [])

    patient = User.objects.get(id=patient_id)
    physician = request.user

    new_todo = ToDo.objects.add_patient_todo(patient, todo_name, due_date)
    if new_todo.problem:
        problem_name = new_todo.problem.problem_name
    else:
        problem_name = ''
    summary = '''Added <u>todo</u> <a href="#/todo/%s"><b>%s</b></a> for <u>problem</u> <b>%s</b>''' % (
        new_todo.id, todo_name, problem_name)
    op_add_todo_event(physician, patient, summary, new_todo)

    #  Todo activities
    actor_profile = UserProfile.objects.get(user=request.user)
    add_todo_activity(new_todo, request.user, "Added this todo.")

    # Add tagged member
    for profile_id in members:
        member = UserProfile.objects.get(id=int(profile_id))
        TaggedToDoOrder.objects.create(todo=new_todo, user=member.user)

        # Set problem authentication
        set_problem_authentication_false(request, new_todo)

        # Save activity
        log = "<b>{0} {1} - {2}</b> joined this todo.".format(member.user.first_name, member.user.last_name,
                                                              member.role)
        add_todo_activity(new_todo, request.user, log)

    resp = {'todo': TodoSerializer(new_todo).data, 'success': True}
    return ajax_response(resp)


@permissions_required(["set_todo_status"])
@login_required
@api_view(["POST"])
#@timeit
def update_todo_status(request, todo_id):
    resp = {'success': False}

    accomplished = request.POST.get('accomplished') == 'true'
    physician = request.user
    # patient = todo.patient

    todo = ToDo.objects.get(id=todo_id)
    todo.accomplished = accomplished
    todo.save(update_fields=["accomplished"])
    # set problem authentication
    set_problem_authentication_false(request, todo)

    problem_name = todo.problem.problem_name if todo.problem else ""
    accomplished_label = 'accomplished' if accomplished else "not accomplished"

    summary = """
    Updated status of <u>todo</u> : <a href="#/todo/{}"><b>{}</b></a> ,
    <u>problem</u> <b>{}</b> to <b>{}</b>
    """.format(todo.id, todo.todo, problem_name, accomplished_label)

    op_add_todo_event(physician, todo.patient, summary, todo)

    actor_profile = UserProfile.objects.get(user=request.user)
    if todo.problem:
        add_problem_activity(todo.problem, request.user, summary, 'output')
        if accomplished:
            op_add_event(physician, todo.patient, summary, todo.problem, True)

    # todo activity
    activity = "Updated status of this todo to <b>{}</b>.".format(accomplished_label)
    add_todo_activity(todo, request.user, activity)

    # todos = ToDo.objects.filter(patient=patient)
    # accomplished_todos = [todo for todo in todos if todo.accomplished]
    # pending_todos = [todo for todo in todos if not todo.accomplished]

    resp['success'] = True
    resp['todo'] = TodoSerializer(todo).data
    # resp['accomplished_todos'] = TodoSerializer(accomplished_todos, many=True).data
    # resp['pending_todos'] = TodoSerializer(pending_todos, many=True).data
    return ajax_response(resp)


@permissions_required(["set_todo_order"])
@login_required
#@timeit
def update_order(request):
    # TODO: Need to understand the logic behind this API -> Tagged todo table are not correct
    """
    " Update ordering of todo(is a specific (virtual list which is determined from other property)list:
    " Patient, Tagged todo, Staff(Personal todo), List todo ??? ) entity
    :param request:
    :return:
    """
    resp = {}
    datas = json.loads(request.body)
    id_todos = datas['todos']
    actor_profile = UserProfile.objects.get(user=request.user)
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
                order = ToDo.objects.filter(patient=patient).aggregate(Max('order'))
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
        add_todo_activity(todo, request.user, activity)
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
                order = TaggedToDoOrder.objects.filter(user=user).aggregate(Max('order'))
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
                order = ToDo.objects.filter(user=user).aggregate(Max('order'))
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
        add_todo_activity(todo, request.user, activity)

    # list todo
    if datas.has_key('list_id'):
        list_id = datas['list_id']
        labeled_list = LabeledToDoList.objects.get(id=int(list_id))
        labeled_list.todo_list = datas['todos']
        labeled_list.save()

    resp['success'] = True
    return ajax_response(resp)


@login_required
#@timeit
def get_todo_info(request, todo_id):
    """
    TODO:
    :param request:
    :param todo_id:
    :return:
    """
    from encounters_app.serializers import EncounterSerializer

    todo_info = ToDo.objects.get(id=todo_id)
    comments = ToDoComment.objects.filter(todo=todo_info)
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

    # Load all document (aka Attachment)
    documents = DocumentTodo.objects.filter(todo=todo_info)
    document_todos_holder = []
    for document in documents:
        document_todos_holder.append(DocumentSerializer(document.document).data)

    encounter_ids = EncounterTodoRecord.objects.filter(todo=todo_info).values_list("encounter__id", flat=True)
    related_encounters = Encounter.objects.filter(id__in=encounter_ids)

    activities = TodoActivity.objects.filter(todo=todo_info)

    sharing_patients = SharingPatient.objects.filter(shared=todo_info.patient).order_by('sharing__first_name',
                                                                                        'sharing__last_name')
    sharing_patients_list = []
    for sharing_patient in sharing_patients:
        user_dict = UserProfileSerializer(sharing_patient.sharing.profile).data
        user_dict['problems'] = [x.id for x in sharing_patient.problems.all()]
        sharing_patients_list.append(user_dict)

    # Update tagged todo status to viewed
    is_tagged = TaggedToDoOrder.objects.filter(user=request.user).filter(todo=todo_info)
    if is_tagged.exists():
        is_tagged.update(status=2)

    resp = {'success': True, 'info': TodoSerializer(todo_info).data,
            'comments': ToDoCommentSerializer(comments, many=True).data, 'attachments': attachment_todos_holder,
            'documents': document_todos_holder,
            'related_encounters': EncounterSerializer(related_encounters, many=True).data,
            'activities': TodoActivitySerializer(activities, many=True).data, 'sharing_patients': sharing_patients_list}
    return ajax_response(resp)


@permissions_required(["add_todo_comment"])
@login_required
#@timeit
def add_todo_comment(request, todo_id):
    resp = {}
    comment = request.POST.get('comment')
    todo_comment = ToDoComment.objects.create(todo_id=todo_id, user=request.user, comment=comment)
    resp['comment'] = ToDoCommentSerializer(todo_comment).data
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["add_todo_comment"])
@login_required
#@timeit
def edit_todo_comment(request, comment_id):
    resp = {}
    comment = request.POST.get('comment')
    todo_comment = ToDoComment.objects.get(id=comment_id)
    todo_comment.comment = comment
    todo_comment.save(update_fields=["comment"])
    resp['comment'] = ToDoCommentSerializer(todo_comment).data
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["delete_todo_comment"])
@login_required
#@timeit
def delete_todo_comment(request, comment_id):
    resp = {}
    ToDoComment.objects.get(id=comment_id).delete()
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["add_todo"])
@login_required
#@timeit
def change_todo_text(request, todo_id):
    resp = {'success': False}

    # Gather input and calculate info
    todo = ToDo.objects.get(id=todo_id)
    todo_text = request.POST.get('todo')
    activity = 'Todo name changed from <b>{0}</b> to <b>{1}</b>'.format(todo.todo, todo_text)

    # Update todo itself
    todo.todo = todo_text
    todo.save(update_fields=["todo"])

    # Save todo activity
    add_todo_activity(todo, request.user, activity)

    # Set problem authentication
    set_problem_authentication_false(request, todo)

    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["add_todo"])
@login_required
#@timeit
def change_todo_due_date(request, todo_id):
    resp = {}
    due_date = request.POST.get('due_date')
    todo = ToDo.objects.get(id=todo_id)
    actor_profile = UserProfile.objects.get(user=request.user)
    if due_date:
        try:
            due_date = parser.parse(due_date, dayfirst=False, ignoretz=True)

            # due_date = datetime.strptime(due_date, '%m/%d/%Y').date()
        except:
            resp['success'] = False
            resp['todo'] = TodoSerializer(todo).data
            return ajax_response(resp)
    else:
        due_date = None

    todo.due_date = due_date
    todo.save(update_fields=["due_date"])

    # set problem authentication
    set_problem_authentication_false(request, todo)

    # todo activity
    if due_date:
        activity = "Changed due date of this todo to <b>%s</b>." % (request.POST.get('due_date'))
    else:
        activity = "Removed due date of this todo."
    add_todo_activity(todo, request.user, activity)

    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["add_todo"])
@login_required
#@timeit
def add_todo_label(request, label_id, todo_id):
    resp = {}
    todo = ToDo.objects.get(id=todo_id)
    label = Label.objects.get(id=label_id)
    todo.labels.add(label)
    # set problem authentication
    set_problem_authentication_false(request, todo)
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["add_todo"])
@login_required
#@timeit
def remove_todo_label(request, label_id, todo_id):
    resp = {}
    label = Label.objects.get(id=label_id)
    todo = ToDo.objects.get(id=todo_id)
    todo.labels.remove(label)
    # set problem authentication
    set_problem_authentication_false(request, todo)
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["add_todo"])
@login_required
#@timeit
def new_todo_label(request, todo_id):
    resp = {}
    resp['status'] = False
    resp['new_status'] = False

    name = request.POST.get('name')
    css_class = request.POST.get('css_class')
    is_all = True if request.POST.get('is_all', False) else False

    if not name == 'screening':
        todo = ToDo.objects.get(id=todo_id)
        label = Label.objects.filter(name=name, css_class=css_class).first()
        if not label:
            label = Label.objects.create(name=name, css_class=css_class,
                                         author=request.user, is_all=is_all)
            resp['new_status'] = True
            resp['new_label'] = LabelSerializer(label).data

        if label.is_all or label.author == request.user:
            if label not in todo.labels.all():
                todo.labels.add(label)
                resp['status'] = True
                resp['label'] = LabelSerializer(label).data

        # set problem authentication
        set_problem_authentication_false(request, todo)
        resp['success'] = True
    return ajax_response(resp)


@permissions_required(["add_todo"])
@login_required
#@timeit
def save_edit_label(request, label_id):
    resp = {}
    resp['status'] = False
    name = request.POST.get('name')
    css_class = request.POST.get('css_class')

    if not name == 'screening':
        label = Label.objects.get(id=label_id)
        if not label.name == 'screening':
            if not Label.objects.filter(name=name, css_class=css_class):
                label.name = name
                label.css_class = css_class
                label.save()
                resp['status'] = True

            resp['label'] = LabelSerializer(label).data
            resp['success'] = True
    return ajax_response(resp)


@permissions_required(["add_todo"])
@login_required
#@timeit
def delete_label(request, label_id):
    resp = {}
    resp['status'] = False

    label = Label.objects.get(id=label_id)
    if not label.name == 'screening':
        label.delete()
        resp['success'] = True
    return ajax_response(resp)


@login_required
#@timeit
def todo_access_encounter(request, todo_id):
    resp = {}
    todo = ToDo.objects.get(id=todo_id)
    physician = request.user
    patient = todo.patient

    if todo.problem:
        summary = '''<a href="#/todo/%s"><b>%s</b></a> for <b>%s</b> was visited.''' % (
            todo.id, todo.todo, todo.problem.problem_name)
    else:
        summary = '''<a href="#/todo/%s"><b>%s</b></a> was visited.''' % (todo.id, todo.todo)

    op_add_todo_event(physician, patient, summary, todo)
    if todo.problem:
        op_add_event(physician, patient, summary, todo.problem, True)

    return ajax_response(resp)


@permissions_required(["add_todo"])
@login_required
@api_view(["POST"])
#@timeit
def add_todo_attachment(request, todo_id):
    attachment = ToDoAttachment.objects.create(todo_id=todo_id, user=request.user, attachment=request.FILES['0'])
    actor_profile = UserProfile.objects.get(user=request.user)
    resp = {}
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
    activity = "Attached <b>%s</b> to this todo." % (attachment.filename())
    add_todo_activity(attachment.todo, request.user, activity, comment=None, attachment=attachment)
    return ajax_response(resp)


#@timeit
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


@permissions_required(["add_todo"])
@login_required
#@timeit
def delete_attachment(request, attachment_id):
    attachment = ToDoAttachment.objects.get(id=attachment_id)
    actor_profile = UserProfile.objects.get(user=request.user)
    # todo activity
    activity = '''
        Deleted <b>%s</b> from this todo.
    ''' % (attachment.filename())
    add_todo_activity(attachment.todo, request.user, activity)
    attachment.delete()

    resp = {}
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["add_todo"])
@login_required
#@timeit
def add_todo_member(request, todo_id):
    """
    TODO: Migrate members relationship to taggedtodoorder table
    :param request:
    :param todo_id:
    :return:
    """
    resp = {}

    todo = ToDo.objects.get(id=todo_id)
    member_id = request.POST.get('id')
    member = UserProfile.objects.get(id=int(member_id))
    tagged_todo = TaggedToDoOrder.objects.filter(todo=todo, user=member.user).first()
    if tagged_todo is None:
        TaggedToDoOrder.objects.create(todo=todo, user=member.user)

        # Set problem authentication
        set_problem_authentication_false(request, todo)

        # Save activity
        log = "<b>{0} {1} - {2}</b> joined this todo.".format(member.user.first_name, member.user.last_name,
                                                              member.role)
        add_todo_activity(todo, request.user, log)

    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["add_todo"])
@login_required
#@timeit
def remove_todo_member(request, todo_id):
    """
    TODO: Migrate members relationship to taggedtodoorder table
    :param request:
    :param todo_id:
    :return:
    """
    resp = {}
    todo = ToDo.objects.get(id=todo_id)
    member_id = request.POST.get('id')
    member = UserProfile.objects.get(id=int(member_id))

    tagged_todo = TaggedToDoOrder.objects.filter(todo=todo, user=member.user).first()
    if tagged_todo:
        tagged_todo.delete()

    # set problem authentication
    set_problem_authentication_false(request, todo)

    # todo activity
    log = "<b>{0} {1} - {2}</b> left this todo.".format(member.user.first_name, member.user.last_name, member.role)
    add_todo_activity(todo, request.user, log)

    resp['success'] = True
    return ajax_response(resp)


@login_required
#@timeit
def get_labels(request, user_id):
    labels = Label.objects.filter(Q(is_all=True) | (Q(is_all=False) & Q(author_id=user_id)))
    resp = {'labels': LabelSerializer(labels, many=True).data}
    return ajax_response(resp)


@login_required
#@timeit
def get_user_todos(request, user_id):
    """
    Get clinical staff todo list \n
    Tagged(which todo user is a member of) \n
    Personal(which todo they are authored) \n
    :param request:
    :param user_id:
    :return:
    """
    resp = {}
    # Load tagged todo which have not yet viewed
    new_tagged_todo_count = TaggedToDoOrder.objects.filter(user_id=user_id).filter(status=0).count()

    tagged_todo_order = TaggedToDoOrder.objects.filter(user_id=user_id).order_by('order', 'todo__due_date')
    tagged_todos = [t.todo for t in tagged_todo_order]
    serialized_data = TodoSerializer(tagged_todos, many=True).data
    for item in serialized_data:
        tagged_todo_instance = TaggedToDoOrder.objects.filter(todo_id=item['id']).filter(user_id=user_id).get()
        item['tagged_status'] = tagged_todo_instance.status

    # Load personal todo list
    personal_todos = ToDo.objects.filter(user_id=user_id).filter(patient=None).order_by('order', 'due_date')

    resp['tagged_todos'] = serialized_data
    resp['new_tagged_todo'] = new_tagged_todo_count
    resp['personal_todos'] = TodoSerializer(personal_todos, many=True).data
    return ajax_response(resp)


@permissions_required(["add_todo"])
@login_required
#@timeit
def add_staff_todo(request, user_id):
    todo_name = request.POST.get('name')
    due_date = request.POST.get('due_date', None)
    if due_date:
        due_date = parser.parse(due_date, dayfirst=False, ignoretz=True)

        # due_date = datetime.strptime(due_date, '%m/%d/%Y').date()

    actor_profile = UserProfile.objects.get(user=request.user)
    new_todo = ToDo.objects.add_staff_todo(user_id, todo_name, due_date)
    # todo activity
    activity = "Added this todo."
    add_todo_activity(new_todo, request.user, activity)

    resp = {}
    resp['todo'] = TodoSerializer(new_todo).data
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["add_todo"])
@login_required
#@timeit
def add_staff_todo_list(request, user_id):
    resp = {'success': False}

    # RETRIEVE DATA SEND FROM FRONT END
    data = json.loads(request.body)
    list_name = data['name']
    labels = data['labels']
    visibility = data['visibility']

    # VALIDATE PERMISSIONS
    # 0: Only for me and 1: For all user
    # If other user role rather than Admin / Physician they can not add Labeled to do list for all user
    if request.user.profile.role not in ['physician', 'admin'] and 0 == visibility:
        return ajax_response(resp)

    # SAVING DATA
    new_list = LabeledToDoList.objects.create(user_id=user_id, name=list_name, private=visibility)

    label_ids = []
    for label in labels:
        l = Label.objects.get(id=label['id'])
        new_list.labels.add(l)
        label_ids.append(l.id)

    todos = ToDo.objects.filter(labels__id__in=label_ids).distinct().order_by('due_date')

    new_list_dict = LabeledToDoListSerializer(new_list).data
    new_list_dict['todos'] = TodoSerializer(todos, many=True).data
    new_list_dict['expanded'] = new_list.expanded

    resp['new_list'] = new_list_dict
    resp['success'] = True
    return ajax_response(resp)


@login_required
#@timeit
def get_user_label_lists(request, user_id):
    
    resp = {}

    lists = LabeledToDoList.objects.filter(user_id=user_id).all()
    
    # Loaded admin labeled to do list for all user
    admin_labeled_todo_list = LabeledToDoList.objects.filter(user__profile__role='admin', private=0).all()

    # Load physician labeled to do list for all user
    physicians = PhysicianTeam.objects.filter(member=request.user)
    physician_ids = [x.physician.id for x in physicians]
    physician_labeled_todo_list = LabeledToDoList.objects.filter(user_id__in=physician_ids).filter(private=0).all()


    merged_list = list(lists) + list(admin_labeled_todo_list) + list(physician_labeled_todo_list)
    lists_holder = []
    
    for label_list in merged_list:
        # list_dict = LabeledToDoListSerializer(label_list).data
        list_dict = dict(label_list.__dict__)
        del list_dict['_state']
        

        # TODO: Have to simplify the below logic, after understand what is being done here.
        label_ids = [l.id for l in label_list.labels.all()]
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
            todo_results = todo_list.get_todo_list_from_label(label_ids)        

        list_dict['todos'] = todo_results
        list_dict['expanded'] = label_list.expanded
        
        lists_holder.append(list_dict)

    resp['todo_lists'] = lists_holder

    return ajax_response(resp)


@permissions_required(["add_todo"])
@login_required
#@timeit
def delete_todo_list(request, list_id):
    resp = {'success': False}
    labeled_to_do_list = LabeledToDoList.objects.get(id=list_id)

    if labeled_to_do_list.user != request.user:
        return ajax_response(resp)

    labeled_to_do_list.delete()
    resp['success'] = True
    return ajax_response(resp)


@login_required
#@timeit
def staff_all_todos(request, user_id):
    resp = {}
    staff = User.objects.get(id=user_id)
    team_members = PhysicianTeam.objects.filter(member_id=user_id)
    physician_ids = [x.physician.id for x in team_members]
    patient_controllers = PatientController.objects.filter(physician__id__in=physician_ids)
    patient_ids = [x.patient.id for x in patient_controllers]
    todos = ToDo.objects.filter(accomplished=False, patient__id__in=patient_ids,
                                due_date__lte=datetime.now()).order_by('-due_date')
    resp['all_todos_list'] = TodoSerializer(todos, many=True).data
    return ajax_response(resp)


@permissions_required(["add_todo"])
@login_required
#@timeit
def open_todo_list(request, list_id):
    resp = {}
    todo_list = LabeledToDoList.objects.get(id=list_id)
    expanded = todo_list.expanded
    data = json.loads(request.body)
    todos = data['todos']

    for todo in todos:
        if not todo['id'] in expanded:
            expanded.append(todo['id'])

    todo_list.expanded = expanded
    todo_list.save()
    resp['success'] = True
    return ajax_response(resp)


@login_required
#@timeit
def batch_save_activities(request):
    """
    TODO: Some how to link with other todo printed in the request
    :param request:
    :return:
    """
    resp = {}
    todo_id_list = request.POST.getlist('todos[]')
    for todo_id in todo_id_list:
        TodoActivity(todo_id=todo_id, author=request.user,
                     activity="<b>{0} {1} - {2} </b> print this todo".format(request.user.first_name,
                                                                             request.user.last_name,
                                                                             request.user.profile.role)).save()

    resp['success'] = True
    return ajax_response(resp)
