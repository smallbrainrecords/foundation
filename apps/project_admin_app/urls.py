from django.conf.urls import patterns, url

urlpatterns = patterns(

    'project_admin_app.views',

    url(r'^$', 'home', name='pa_home'),

    url(r'^list/registered/users/$', 'list_registered_users', name='pa_list_registered_users'),

    url(r'^list/unregistered/users/$', 'list_unregistered_users', name='pa_list_unregistered_users'),

    url(r'^user/(?P<user_id>\d+)/info/$', 'user_info', name='pa_user_info'),

    url(r'^user/approve/$', 'approve_user', name='pa_approve_user'),

    url(r'^user/reject/$', 'reject_user', name='pa_reject_user'),

    url(r'^user/update/profile/$', 'update_profile', name='pa_update_profile'),

    url(r'^user/update/basic/$', 'update_basic_profile', name='pa_update_basic_profile'),

    url(r'^user/update/email/$', 'update_email', name='pa_update_email'),

    url(r'^user/update/password/$', 'update_password', name='pa_update_password'),

    url(r'^user/update/active/$', 'update_active', name='pa_update_active'),

    url(r'^user/update/deceased_date/$', 'update_deceased_date', name='pa_update_deceased_date'),

    url(r'^user/create/$', 'create_user', name='pa_create_user'),

    url(r'^patient/physicians/$', 'list_patient_physicians', name='pa_list_patient_physicians'),

    url(r'^assigned/physicians/$', 'list_assigned_physicians', name='pa_list_assigned_physicians'),

    url(r'^physician/data/$', 'fetch_physician_data', name='pa_fetch_physician_data'),

    url(r'^physician/assign/member/$', 'assign_physician_member', name='pa_assign_physician_member'),

    url(r'^physician/unassign/member/$', 'unassign_physician_member', name='pa_unassign_physician_member'), )
