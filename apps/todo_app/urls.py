from django.conf.urls import patterns, include, url


urlpatterns = patterns('todo_app.views',

    url(r'^patient/(?P<patient_id>\d+)/todos/add/new_todo$', 'add_patient_todo'),
    url(r'^staff/(?P<user_id>\d+)/todos/add/new_todo$', 'add_staff_todo'),
    url(r'^staff/(?P<user_id>\d+)/new_list$', 'add_staff_todo_list'),

    url(r'^todo/(?P<todo_id>\d+)/update/$', 'update_todo_status'),
    url(r'^todo/updateOrder/$', 'update_order'),
    url(r'^todo/(?P<todo_id>\d+)/info/$', 'get_todo_info'),
    url(r'^todo/(?P<todo_id>\d+)/comment$', 'add_todo_comment'),
    url(r'^todo/(?P<comment_id>\d+)/edit$', 'edit_todo_comment'),
    url(r'^todo/(?P<comment_id>\d+)/delete$', 'delete_todo_comment'),
    url(r'^todo/(?P<todo_id>\d+)/changeText$', 'change_todo_text'),
    url(r'^todo/(?P<todo_id>\d+)/changeDueDate$', 'change_todo_due_date'),
    url(r'^todo/(?P<label_id>\d+)/(?P<todo_id>\d+)/addLabel$', 'add_todo_label'),
    url(r'^todo/removeLabel/(?P<label_id>\d+)/(?P<todo_id>\d+)$', 'remove_todo_label'),
    url(r'^todo/deleteLabel/(?P<label_id>\d+)$', 'delete_label'),
    url(r'^todo/newLabel/(?P<todo_id>\d+)$', 'new_todo_label'),
    url(r'^todo/accessEncounter/(?P<todo_id>\d+)$', 'todo_access_encounter'),
    url(r'^todo/(?P<todo_id>\d+)/addAttachment$', 'add_todo_attachment'),
    url(r'^attachment/(?P<attachment_id>\d+)/downloadAttachment$', 'download_attachment'),
    url(r'^attachment/(?P<attachment_id>\d+)/delete$', 'delete_attachment'),
    url(r'^todo/(?P<todo_id>\d+)/activity/$','get_todo_activity'),
    url(r'^todo/(?P<todo_id>\d+)/addMember$', 'add_todo_member'),
    url(r'^todo/(?P<todo_id>\d+)/removeMember$', 'remove_todo_member'),
    url(r'^todo/(?P<user_id>\d+)/getlabels$', 'get_labels'),
    url(r'^todo/(?P<user_id>\d+)/getLabeledTodoList$', 'get_user_label_lists'),
    url(r'^todo/saveEditLabel/(?P<label_id>\d+)$', 'save_edit_label'),
    url(r'^todo/user_todos/(?P<user_id>\d+)$', 'get_user_todos'),
    url(r'^todo/(?P<list_id>\d+)/deleteTodoList$', 'delete_todo_list'),
)
