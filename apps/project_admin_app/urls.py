from django.conf.urls import patterns, include, url

urlpatterns = patterns('project_admin_app.views',

	url(r'^$', 'home', name='pa_home'),

	url(r'^list/registered/users/$', 'list_registered_users', name='pa_list_registered_users'),

	url(r'^list/unregistered/users/$', 'list_unregistered_users', name='pa_list_unregistered_users'),

	url(r'^user/(?P<user_id>\d+)/info/$', 'user_info', name='pa_user_info'),

	url(r'^user/approve/$', 'approve_user', name='pa_approve_user'),

	url(r'^user/update/profile/$', 'update_profile', name='pa_update_profile'),

	url(r'^user/update/basic/$', 'update_basic_profile', name='pa_update_basic_profile'),

	url(r'^user/update/email/$', 'update_email', name='pa_update_email'),

	url(r'^user/update/password/$', 'update_password', name='pa_update_password'),

)