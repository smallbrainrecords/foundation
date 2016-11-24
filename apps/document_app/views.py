from common.views import *
from document_app.serializers import *
from emr.models import Document, DocumentTodo, DocumentProblem, ToDo, Problem, UserProfile


# Handle uploaded document file by file
@login_required
def upload_document(request):
    resp = {'success': False}

    document = request.FILES['file']

    documentDAO = Document.objects.create(author=request.user.profile, document=document)
    documentDAO.save()

    # TODO
    resp['document'] = documentDAO.id
    resp['success'] = True
    return ajax_response(resp)


@login_required
def document_list(request):
    resp = {'success': False}

    documents = Document.objects.all()

    resp['documents'] = DocumentSerialization(documents, many=True).data
    resp['success'] = True

    return ajax_response(resp)


# TODO: Check access here
@login_required
def document_info(request, document_id):
    resp = {'success': False}

    document = Document.objects.filter(id=document_id).get()

    resp['info'] = DocumentSerialization(document).data
    resp['success'] = True
    return ajax_response(resp)


@login_required
def pin_patient_2_document(request):
    resp = {'success': False}
    json_body = json.loads(request.body)
    document_id = json_body.get('document')

    # Remove related
    Document.objects.filter(id=document_id).update(patient_id=json_body.get('patient'))
    DocumentTodo.objects.filter(document=document_id).delete()
    DocumentProblem.objects.filter(document=document_id).delete()

    resp['success'] = True
    return ajax_response(resp)


@login_required
def pin_todo_2_document(request):
    resp = {'success': False}
    json_body = json.loads(request.body)
    document = Document.objects.filter(id=json_body.get('document')).get()
    todo = ToDo.objects.filter(id=json_body.get('todo')).get()

    DocumentTodo.objects.create(document=document, todo=todo)

    resp['success'] = True
    return ajax_response(resp)


@login_required
def pin_problem_2_document(request):
    resp = {'success': False}
    json_body = json.loads(request.body)
    document = Document.objects.filter(id=json_body.get('document')).get()
    problem = Problem.objects.filter(id=json_body.get('problem')).get()
    DocumentProblem.objects.create(document=document, problem=problem)

    resp['success'] = True
    return ajax_response(resp)


@login_required
def search_patient(request):
    resp = {'success': False}
    json_body = json.loads(request.body)

    items = User.objects.filter(first_name__contains=json_body.get('search_str'),
                                last_name__contains=json_body.get('search_str'))

    resp['results'] = SafeUserSerializer(items, many=True).data
    resp['success'] = True
    return ajax_response(resp)


@login_required
def get_patient_document(request, patient_id):
    resp = {'success': False}

    items = Document.objects.filter(patient_id=patient_id)

    resp['info'] = DocumentSerialization(items, many=True).data
    resp['success'] = True
    return ajax_response(resp)
