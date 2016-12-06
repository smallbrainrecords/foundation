from django.db.models import Prefetch

from common.views import *
from document_app.serializers import *
from emr.models import Document, DocumentTodo, DocumentProblem, ToDo, Problem, UserProfile, Label

#
from problems_app.serializers import ProblemInfoSerializer
from todo_app.serializers import LabelSerializer


@login_required
def upload_document(request):
    """
    Handle single document file uploaded
    :param request:
    :return:
    """
    resp = {'success': False}

    document = request.FILES['file']
    author = request.POST.get('author', None)
    patient = request.POST.get('patient', None)

    document_dao = Document.objects.create(author_id=author, document=document, patient_id=patient)
    document_dao.save()

    # TODO
    resp['document'] = document_dao.id
    resp['success'] = True
    return ajax_response(resp)


@login_required
def document_list(request):
    """
    Handle single file upload
    :param request:
    :return:
    """
    resp = {'success': False}

    documents = Document.objects.all()
    resp['documents'] = DocumentSerialization(documents, many=True).data
    resp['success'] = True

    return ajax_response(resp)


# TODO: Check access here
@login_required
def document_info(request, document_id):
    """

    :param request:
    :param document_id:
    :return:
    """
    resp = {'success': False}

    document = Document.objects.filter(id=document_id).get()
    labels = Label.objects.filter(
        is_all=True)  # Get all label is saved all for user. Refer to https://trello.com/c/OtAAk09y

    resp['info'] = DocumentSerialization(document).data
    resp['labels'] = LabelSerializer(labels, many=True).data
    resp['success'] = True
    return ajax_response(resp)


@login_required
def pin_patient_2_document(request):
    """

    :param request:
    :return:
    """
    resp = {'success': False}
    json_body = json.loads(request.body)
    document_id = json_body.get('document')
    patient_id = json_body.get('patient')
    # Remove related
    Document.objects.filter(id=document_id).update(patient=UserProfile.objects.filter(id=patient_id).get())
    DocumentTodo.objects.filter(document=document_id).delete()
    DocumentProblem.objects.filter(document=document_id).delete()

    document = Document.objects.filter(id=document_id).get()

    resp['info'] = DocumentSerialization(document).data
    resp['success'] = True
    return ajax_response(resp)


@login_required
def pin_todo_2_document(request):
    """

    :param request:
    :return:
    """
    resp = {'success': False}
    json_body = json.loads(request.body)
    document = Document.objects.filter(id=json_body.get('document')).get()
    todo = ToDo.objects.filter(id=json_body.get('todo')).get()

    DocumentTodo.objects.create(document=document, todo=todo, author=request.user.profile)

    resp['success'] = True
    return ajax_response(resp)


@login_required
def pin_problem_2_document(request):
    """

    :param request:
    :return:
    """

    resp = {'success': False}
    json_body = json.loads(request.body)
    document = Document.objects.filter(id=json_body.get('document')).get()
    problem = Problem.objects.filter(id=json_body.get('problem')).get()

    DocumentProblem.objects.create(document=document, problem=problem, author=request.user.profile)

    resp['success'] = True
    return ajax_response(resp)


@login_required
def search_patient(request):
    """

    :param request:
    :return:
    """
    resp = {'success': False}
    result = []
    json_body = json.loads(request.body)

    items = UserProfile.objects.filter(role='patient')

    for item in items:
        if unicode(item).__contains__(json_body.get('search_str')):
            result.append({
                'uid': item.id,
                'full_name': unicode(item)
            })

    resp['results'] = result
    resp['success'] = True
    return ajax_response(resp)


@login_required
def get_patient_document(request, patient_id):
    """

    :param request:
    :param patient_id:
    :return:
    """
    resp = {'success': False}
    profile = UserProfile.objects.filter(user_id=patient_id)
    items = Document.objects.filter(patient=profile)

    resp['info'] = DocumentSerialization(items, many=True).data
    resp['success'] = True
    return ajax_response(resp)


@login_required
def delete_document(request, document_id):
    """
    A patient can delete a document that they 'attached' to a todo or uploaded.\n
    A patient can NOT delete a document that was attached to a todo or uploaded by any other user.\n
    A patient can NOT delete a document that was uploaded unless the patient uploaded that document himself.\n
    A doctor, nurse, secretary, mid-level and admin may delete a document that was uploaded.\n
    IF a document has been "attached" to a todo in the 'tagging' page then it can be deleted from a todo by a doctor or admin.\n
    A pop up will ask "Remove this document from the todo only" or "Delete this document from the todo and the system"\n
    If the user selects 'from the todo only' then the document will not be displayed on the todo like an attachment\n
    but that document will still be in the document page (it will lose labels and association with that todo).\n
    If the user selects "delete.. and the system" then the document is deleted completely.
    :param document_id:
    :param request:
    :return:
    """

    resp = {'success': False}
    json_body = json.loads(request.body)

    user = request.user  # Current logged in user
    document_id = json_body.get('document')  # Document which will be deleted
    del_tag_id = json_body.get('del_tag_id')  # Tagging id
    del_tag_type = json_body.get('del_tag_type')  # Tagging type will be a problem or a todo
    del_in_sys = json_body.get('del_in_sys')  # Flag if document is remove from the system

    document = Document.objects.filter(id=document_id).get()
    if del_tag_type == 'problem':
        problem = Problem.objects.filter(id=del_tag_id).get()
        tag = DocumentProblem.objects.filter(document=document, problem=problem).get()
    else:
        todo = ToDo.objects.filter(id=del_tag_id).get()
        tag = DocumentTodo.objects.filter(document=document, todo=todo).get()

    if user.profile.role != 'patient':
        tag.delete()
    else:
        if user.profile == document.author:
            tag.delete()

    if del_in_sys and ["physician", "admin"].__contains__(user.profile.role):
        document.delete()

    resp['success'] = True
    return ajax_response(resp)


@login_required
def document_list_by_problem(request, problem_id):
    """

    :param request:
    :param problem_id:
    :return:
    """
    resp = {'success': False}

    # Loading problem info
    problem_info = Problem.objects.prefetch_related(
        Prefetch("todo_set", queryset=ToDo.objects.order_by("order"))
    ).get(id=problem_id)

    # Loading document pinned directly to problem
    document_probs = DocumentProblem.objects.filter(problem=problem_info)
    document_probs_serialized = DocumentProblemSerialization(document_probs, many=True).data
    document_probs_list = [doc['document'] for doc in document_probs_serialized]
    document_probs_pk = [doc['id'] for doc in
                         document_probs_list]  # Used for remove duplicated document also pinned to the todo

    # Loading document pinned via todo (which is pinned to problem), remove duplicated document already pinned problem.
    # TODO: Two pinned todos both are pinned same documentation filtering
    problem_serialized = ProblemInfoSerializer(problem_info).data
    todos_pk = [todo['id'] for todo in problem_serialized['problem_todos']]
    document_todos = DocumentTodo.objects.filter(todo_id__in=todos_pk).exclude(document_id__in=document_probs_pk)
    document_todos_list = [doc['document'] for doc in DocumentTodoSerialization(document_todos, many=True).data]

    # Need remove duplicated and sorted by creation date
    resp['documents'] = document_probs_list + document_todos_list
    resp['success'] = True
    return ajax_response(resp)


@login_required
def pin_label_2_document(request):
    """
    Pin a label to a document
    :param request:
    :return:
    """
    resp = {'success': False}
    json_body = json.loads(request.body)
    document_id = json_body.get('document')
    document = Document.objects.get(id=document_id)
    label_id = json_body.get('label')
    label = Label.objects.get(id=label_id)
    document.labels.add(label)

    resp['success'] = True
    return ajax_response(resp)


@login_required
def remove_document_label(request):
    """
    Pin a label to a document
    :param request:
    :return:
    """
    resp = {'success': False}
    json_body = json.loads(request.body)
    document_id = json_body.get('document')
    document = Document.objects.get(id=document_id)
    label_id = json_body.get('label')
    label = Label.objects.get(id=label_id)
    document.labels.remove(label)

    resp['success'] = True
    return ajax_response(resp)
