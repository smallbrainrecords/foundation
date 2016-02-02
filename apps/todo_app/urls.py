from django.conf.urls import patterns, include, url


urlpatterns = patterns('todo_app.views',

    url(r'^patient/(?P<patient_id>\d+)/todos/add/new_todo$', 'add_patient_todo'),

    url(r'^todo/(?P<todo_id>\d+)/update/$', 'update_todo_status'),
    url(r'^todo/updateOrder/$', 'update_order'),
    url(r'^todo/(?P<todo_id>\d+)/info/$', 'get_todo_info'),
    url(r'^todo/(?P<todo_id>\d+)/comment$', 'add_todo_comment'),
    url(r'^todo/(?P<comment_id>\d+)/edit$', 'edit_todo_comment'),
    url(r'^todo/(?P<comment_id>\d+)/delete$', 'delete_todo_comment'),
)
