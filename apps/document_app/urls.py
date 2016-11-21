from django.conf.urls import url, patterns
from document_app import views

urlpatterns = patterns('document_app.views',
                       url(r'^upload_document$', "upload_document"),
                       url(r'^list', "document_list")
                       )
