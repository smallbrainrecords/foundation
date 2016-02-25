from django.conf.urls import patterns, include, url


urlpatterns = patterns('todo_app.views',

    url(r'^patient/(?P<patient_id>\d+)/todos/add/new_todo$', 'add_patient_todo'),

    url(r'^todo/(?P<todo_id>\d+)/update/$', 'update_todo_status'),
    url(r'^todo/updateOrder/$', 'update_order'),
    url(r'^todo/(?P<todo_id>\d+)/info/$', 'get_todo_info'),
    url(r'^todo/(?P<todo_id>\d+)/comment$', 'add_todo_comment'),
    url(r'^todo/(?P<comment_id>\d+)/edit$', 'edit_todo_comment'),
    url(r'^todo/(?P<comment_id>\d+)/delete$', 'delete_todo_comment'),
    url(r'^todo/(?P<todo_id>\d+)/changeText$', 'change_todo_text'),
    url(r'^todo/(?P<todo_id>\d+)/changeDueDate$', 'change_todo_due_date'),
    url(r'^todo/(?P<todo_id>\d+)/addLabel$', 'add_todo_label'),
    url(r'^todo/removeLabel/(?P<label_id>\d+)$', 'remove_todo_label'),
    url(r'^todo/accessEncounter/(?P<todo_id>\d+)$', 'todo_access_encounter'),
    url(r'^todo/(?P<todo_id>\d+)/addAttachment$', 'add_todo_attachment'),
    url(r'^attachment/(?P<attachment_id>\d+)/downloadAttachment$', 'download_attachment'),
    url(r'^attachment/(?P<attachment_id>\d+)/delete$', 'delete_attachment'),
    url(r'^todo/(?P<todo_id>\d+)/activity/$','get_todo_activity'),
)
