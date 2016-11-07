from django.conf.urls import patterns, include, url


urlpatterns = patterns('inr_app.views',
    url(r'^(?P<patient_id>\d+)/(?P<problem_id>\d+)/get_inrs$', 'get_inrs'),
    url(r'^(?P<inr_id>\d+)/set_target$', 'set_target'),
    url(r'^get_list_problem$', 'get_list_problem'),
    url(r'^save_inrvalue$', 'save_inrvalue'),
)
