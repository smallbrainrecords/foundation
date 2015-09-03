from django.conf.urls import patterns, url


urlpatterns = patterns(
    'users_app.views',
    url(r'^login/$', 'login_user'),
    url(r'^logout/$', 'logout_user'),
    url(r'^register/$', 'register_user'),
    url(r'^home/$', 'home'),
    url(r'^staff/$', 'staff'),
    url(r'^patient/manage/(?P<user_id>\d+)/$', 'manage_patient'),
    url(r'^patient/(?P<patient_id>\d+)/info$', 'get_patient_info'),

    url(
        r'^patient/(?P<patient_id>\d+)/profile/update_summary$',
        'update_patient_summary'),

    url(r'^active/user/$', 'fetch_active_user'),)
