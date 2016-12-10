from django.conf.urls import patterns, include, url

urlpatterns = patterns('inr_app.views',
                       url(r'^(?P<patient_id>\d+)/(?P<problem_id>\d+)/get_inrs$', 'get_inrs'),
                       url(r'^(?P<inr_id>\d+)/set_target$', 'set_target'),
                       url(r'^(?P<inr_id>\d+)/edit_inrvalue$', 'edit_inrvalue'),
                       url(r'^(?P<inr_id>\d+)/delete_inrvalue$', 'delete_inrvalue'),
                       url(r'^get_list_problem$', 'get_list_problem'),
                       url(r'^save_inrvalue$', 'save_inrvalue'),
                       url(r'^add_note$', 'add_note'),
                       )
