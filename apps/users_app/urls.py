from django.conf.urls import patterns, include, url


urlpatterns = patterns('users_app.views',

	url(r'^patient/manage/(?P<user_id>\d+)/$', 'manage_patient'),
    url(r'^patient/(?P<patient_id>\d+)/info$', 'get_patient_info'),
    url(r'^patient/(?P<patient_id>\d+)/profile/update_summary$', 'update_patient_summary'),

	)

