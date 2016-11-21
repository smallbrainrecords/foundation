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
    # documents_list = []
    # for document in documents:
    #     documents_list.append()

    resp['documents'] = DocumentSerialization(documents,many=True).data
    resp['success'] = True

    return ajax_response(resp)
