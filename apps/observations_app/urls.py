from django.conf.urls import patterns, include, url


urlpatterns = patterns('observations_app.views',

    url(r'^(?P<observation_id>\d+)/info$', 'get_observation_info'),
    url(r'^(?P<component_id>\d+)/component_info$', 'get_observation_component_info'),
    url(r'^(?P<observation_id>\d+)/add_note$', 'add_note'),
    url(r'^(?P<observation_id>\d+)/add_value$', 'add_value'),
    url(r'^(?P<observation_id>\d+)/patient_refused$', 'patient_refused'),
    url(r'^note/(?P<note_id>\d+)/edit$', 'edit_note'),
    url(r'^note/(?P<note_id>\d+)/delete$', 'delete_note'),
    url(r'^component/(?P<component_id>\d+)/delete$', 'delete_component'),
    url(r'^component/(?P<component_id>\d+)/edit$', 'edit_component'),
    url(r'^component/(?P<component_id>\d+)/add_note$', 'add_component_note'),
    url(r'^component/note/(?P<note_id>\d+)/edit$', 'edit_component_note'),
    url(r'^component/note/(?P<note_id>\d+)/delete$', 'delete_component_note'),
    url(r'^(?P<observation_id>\d+)/track/click/$',
        'track_observation_click'),
)
