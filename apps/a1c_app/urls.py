from django.conf.urls import patterns, include, url


urlpatterns = patterns('a1c_app.views',

    url(r'^(?P<a1c_id>\d+)/info$', 'get_a1c_info'),
    url(r'^(?P<value_id>\d+)/value_info$', 'get_observation_value_info'),
    url(r'^(?P<a1c_id>\d+)/add_note$', 'add_note'),
    url(r'^(?P<component_id>\d+)/add_value$', 'add_value'),
    url(r'^(?P<a1c_id>\d+)/patient_refused$', 'patient_refused'),
    url(r'^note/(?P<note_id>\d+)/edit$', 'edit_note'),
    url(r'^note/(?P<note_id>\d+)/delete$', 'delete_note'),
    url(r'^value/(?P<value_id>\d+)/delete$', 'delete_value'),
    url(r'^value/(?P<value_id>\d+)/edit$', 'edit_value'),
    url(r'^value/(?P<value_id>\d+)/add_note$', 'add_value_note'),
    url(r'^value/note/(?P<note_id>\d+)/edit$', 'edit_value_note'),
    url(r'^value/note/(?P<note_id>\d+)/delete$', 'delete_value_note'),
    url(r'^(?P<a1c_id>\d+)/track/click/$',
        'track_a1c_click'),
)
