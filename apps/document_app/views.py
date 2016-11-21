from common.views import *
from document_app.serializers import DocumentSerialization
from emr.models import Document


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
