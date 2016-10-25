from django.conf.urls import patterns, include, url


urlpatterns = patterns('medication_app.views',
    url(r'^list_terms$', 'list_terms'),
    url(r'^(?P<patient_id>\d+)/get_medications$', 'get_medications'),
    url(r'^(?P<patient_id>\d+)/add_medication$', 'add_medication'),
    url(r'^(?P<patient_id>\d+)/(?P<medication_id>\d+)/add_medication_note$', 'add_medication_note'),
    url(r'^note/(?P<note_id>\d+)/edit$', 'edit_note'),
    url(r'^note/(?P<note_id>\d+)/delete$', 'delete_note'),
    url(r'^(?P<patient_id>\d+)/medication/(?P<medication_id>\d+)/info$', 'get_medication'),
    url(r'^(?P<medication_id>\d+)/get_pins$', 'get_pins'),
    url(r'^(?P<patient_id>\d+)/pin_to_problem$', 'pin_to_problem'),
    url(r'^(?P<patient_id>\d+)/(?P<medication_id>\d+)/change_active_medication$', 'change_active_medication'),
)
