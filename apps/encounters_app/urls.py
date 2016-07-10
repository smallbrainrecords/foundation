from django.conf.urls import patterns, include, url


urlpatterns = patterns('encounters_app.views',

    url(r'^patient/(?P<patient_id>\d+)/encounter/status$', 'patient_encounter_status'),
    url(r'^patient/(?P<patient_id>\d+)/encounter/start$', 'create_new_encounter'),
    url(r'^encounter/(?P<encounter_id>\d+)/info$', 'get_encounter_info'),
    url(r'^encounter/(?P<encounter_id>\d+)/stop$', 'stop_patient_encounter'),
    url(r'^encounter/add/event_summary$', 'add_event_summary'),
    url(r'^patient/(?P<patient_id>\d+)/encounter/(?P<encounter_id>\d+)/update_note$', 'update_encounter_note'),
    url(r'^patient/(?P<patient_id>\d+)/encounter/(?P<encounter_id>\d+)/upload_video/$', 'upload_encounter_video'),
    url(r'^patient/(?P<patient_id>\d+)/encounter/(?P<encounter_id>\d+)/upload_audio/$', 'upload_encounter_audio'),
    url(r'^patient/(?P<patient_id>\d+)/encounter/(?P<encounter_id>\d+)/add_timestamp$', 'add_timestamp'),
    url(r'^encounter_event/(?P<encounter_event_id>\d+)/mark_favorite$', 'mark_favorite'),
    url(r'^encounter_event/(?P<encounter_event_id>\d+)/name_favorite$', 'name_favorite'),
	)
