from django.conf.urls import patterns, include, url


urlpatterns = patterns('inr_app.views',
    url(r'^(?P<patient_id>\d+)/get_inr$', 'get_inr'),
    url(r'^(?P<patient_id>\d+)/(?P<inr_id>\d+)/add_medication$', 'add_medication'),
    url(r'^(?P<patient_id>\d+)/(?P<medication_id>\d+)/add_medication_note$', 'add_medication_note'),
    url(r'^note/(?P<note_id>\d+)/edit$', 'edit_note'),
    url(r'^note/(?P<note_id>\d+)/delete$', 'delete_note'),
    url(r'^(?P<patient_id>\d+)/medication/(?P<medication_id>\d+)/info$', 'get_medication'),
    url(r'^medication/(?P<medication_id>\d+)/get_pins$', 'get_pins'),
    url(r'^medication/(?P<patient_id>\d+)/pin_to_problem$', 'pin_to_problem'),
)
