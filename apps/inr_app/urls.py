from django.conf.urls import patterns, include, url


urlpatterns = patterns('inr_app.views',
    url(r'^(?P<patient_id>\d+)/(?P<problem_id>\d+)/get_inrs$', 'get_inrs'),
)
