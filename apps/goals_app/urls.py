from django.conf.urls import patterns, include, url


urlpatterns = patterns('goals_app.views',

    url(r'^goal/(?P<goal_id>\d+)/info$', 'get_goal_info'),
    url(r'^patient/(?P<patient_id>\d+)/goals/add/new_goal$', 'add_patient_goal'),
    url(r'^patient/(?P<patient_id>\d+)/goal/(?P<goal_id>\d+)/add_note$', 'add_goal_note'),
    url(r'^patient/(?P<patient_id>\d+)/goal/(?P<goal_id>\d+)/update_status$', 'update_goal_status'),

	)