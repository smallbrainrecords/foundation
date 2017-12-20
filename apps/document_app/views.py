from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q

from common.views import *
from document_app.serializers import *
from emr.models import Document, DocumentTodo, DocumentProblem, ToDo, Problem, UserProfile, Label
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
    # TODO: Currently this is using patient profile id instead of user id
    # Change from UserProfile's id to User's id
    # author = request.POST.get('author', None)
    # author_user = User.objects.filter(profile__id=author).first()

    # TODO: Currently this is using patient profile id instead of user id
    # Change from UserProfile's id to User's id
    patient_uid = request.POST.get('patient', None)
    # patient_user = User.objects.filter(profile__id=patient).first()

    document_dao = Document.objects.create(document=document, document_name=document.name,
                                           patient_id=patient_uid, author=request.user)
    document_dao.save()

    resp['document'] = document_dao.id
    resp['success'] = True
    return ajax_response(resp)


@login_required
def get_document_list(request):
    """
    Return uploaded document
    :param request:
    :param page
    :return:
    """
    resp = {'success': False}
    page = request.GET['page']
    show_document_has_patient_pinned = request.GET['show_pinned']

    page = int(page) - 1
    item_per_page = 10

    if 'false' == show_document_has_patient_pinned:
        documents = Document.objects.filter(patient__isnull=True).order_by('-created_on')
    else:
        documents = Document.objects.order_by('-created_on')

    result_set = documents.all()[page * item_per_page: page * item_per_page + item_per_page]

    resp['documents'] = DocumentListSerializer(result_set, many=True).data
    resp['total'] = documents.count()
    resp['success'] = True

    return ajax_response(resp)


@login_required
def document_info(request, document_id):
    """

    :param request:
    :param document_id:
    :return:
    """
    resp = {'success': False}

    document = Document.objects.filter(id=document_id).get()

    labels = Label.objects.filter(is_all=True)

    resp['info'] = DocumentSerializer(document).data
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
    patient_uid = json_body.get('patient')  # User id
    # Remove related
    Document.objects.filter(id=document_id).update(patient_id=patient_uid)
    DocumentTodo.objects.filter(document=document_id).delete()
    DocumentProblem.objects.filter(document=document_id).delete()

    document = Document.objects.filter(id=document_id).get()

    resp['info'] = DocumentSerializer(document).data
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

    DocumentTodo.objects.create(document=document, todo=todo, author=request.user)

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

    DocumentProblem.objects.create(document=document, problem=problem, author=request.user)

    resp['success'] = True
    return ajax_response(resp)


@login_required
def search_patient(request):
    """
    Type ahead result to search patient
    :param request:
    :return:
    """
    resp = {'success': False}
    result = []
    json_body = json.loads(request.body)
    search_str = json_body.get('search_str')

    profiles = UserProfile.objects.filter(role='patient').filter(
        Q(user__first_name__icontains=search_str)
        | Q(user__last_name__icontains=search_str)
    )

    for profile in profiles:
        result.append({
            'uid': profile.user.id,
            'full_name': unicode(profile)
        })

    resp['results'] = result
    resp['success'] = True
    return ajax_response(resp)


@login_required
def get_patient_document(request, patient_id):
    """

    :param request:
    :param patient_id: Patient user id
    :return:
    """
    resp = {'success': False}
    user = User.objects.filter(id=patient_id).first()
    items = Document.objects.filter(patient=user)

    resp['info'] = DocumentSerializer(items, many=True).data
    resp['success'] = True
    return ajax_response(resp)


@login_required
def delete_document(request, document_id):
    """
    ONLY DELETE DOCUMENT FROM TODO'S PAGE
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

    if user.profile.role != 'patient':  # Other user not patient can delete the tag without hassle
        tag.delete()
    else:
        # Patient can only delete tag if they document owner or tag author
        if user.profile == document.author or user.profile == tag.author:
            tag.delete()

    if del_in_sys and ["physician", "admin"].__contains__(user.profile.role):  # delete document in system
        document.delete()

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
    label_id = json_body.get('label')

    document = Document.objects.get(id=document_id)
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
    label_id = json_body.get('label')

    document = Document.objects.get(id=document_id)
    label = Label.objects.get(id=label_id)
    document.labels.remove(label)

    resp['success'] = True
    return ajax_response(resp)


@login_required
def unpin_document_todo(request):
    """

    :param request:
    :return:
    """
    resp = {'success': False}
    json_body = json.loads(request.body)
    document_id = json_body.get('document')
    todo_id = json_body.get('todo')

    DocumentTodo.objects.filter(document_id=document_id).filter(todo_id=todo_id).delete()

    resp['success'] = True
    return ajax_response(resp)


@login_required
def unpin_document_problem(request):
    """
    Unpin a problem from document
    :param request:
    :return:
    """
    resp = {'success': False}
    json_body = json.loads(request.body)
    problem_id = json_body.get('problem')
    document_id = json_body.get('document')

    DocumentProblem.objects.filter(document_id=document_id).filter(problem_id=problem_id).delete()

    resp['success'] = True
    return ajax_response(resp)


@login_required
def remove_document(request, document_id):
    """
    Delete a document from system
    TODO: Need to remove file from system
    :param document_id:
    :param request:
    :return:
    """
    resp = {'success': False}

    document = Document.objects.filter(id=document_id).get()

    # Patient cannot delete document uploaded by the other
    if request.user.profile.role == 'patient' and request.user != document.author:
        resp['message'] = "You don't have permission to do this action"
        return ajax_response(resp)

    document.delete()

    resp['success'] = True
    return ajax_response(resp)


@login_required
def update_name(request, document_id):
    """
    Rename document name. Allow duplicated file name(aka display name)
    :param document_id:
    :param request:
    :return:
    """
    resp = {'success': False}
    json_body = json.loads(request.body)
    document_name = json_body.get('name')

    # Validate new name is not empty
    if "" == document_name or document_name is None:
        resp['message'] = "File name is required"
        return ajax_response(resp)

    document = Document.objects.get(id=document_id)
    if document:
        document.document_name = "{0}.{1}".format(document_name, document.file_extension_lower())
        document.save()

    resp['success'] = True
    return ajax_response(resp)
