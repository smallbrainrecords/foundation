from django.conf.urls import patterns, include, url


urlpatterns = patterns('data_app.views',
	url(r'^(?P<observation_id>\d+)/info$', 'get_observation_info'),
    url(r'^(?P<patient_id>\d+)/get_datas$', 'get_datas'),
)
