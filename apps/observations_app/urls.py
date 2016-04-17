from django.conf.urls import patterns, include, url


urlpatterns = patterns('observations_app.views',

    url(r'^(?P<observation_id>\d+)/info$', 'get_observation_info'),
    url(r'^(?P<observation_id>\d+)/add_note$', 'add_note'),
    url(r'^(?P<observation_id>\d+)/add_value$', 'add_value'),
    url(r'^note/(?P<note_id>\d+)/edit$', 'edit_note'),
    url(r'^note/(?P<note_id>\d+)/delete$', 'delete_note'),
)
