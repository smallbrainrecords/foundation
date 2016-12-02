from django.conf.urls import url, patterns

urlpatterns = patterns('document_app.views',
                       url(r'^upload_document$', "upload_document"),
                       url(r'^list', "document_list"),
                       url(r'^info/(?P<document_id>\d+)$', 'document_info'),
                       url(r'^pin/patient', 'pin_patient_2_document'),
                       url(r'^pin/todo', 'pin_todo_2_document'),
                       url(r'^pin/problem', 'pin_problem_2_document'),
                       url(r'^search_patient', 'search_patient'),
                       url(r'^(?P<patient_id>\d+)/get_pinned_document', 'get_patient_document'),
                       url(r'^delete/(?P<document_id>\d+)$', 'delete_document'),
                       url(r'^problem/(?P<problem_id>\d+)$', 'document_list_by_problem')
                       )
