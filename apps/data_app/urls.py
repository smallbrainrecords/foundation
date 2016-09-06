from django.conf.urls import patterns, include, url


urlpatterns = patterns('data_app.views',
	url(r'^track/click$', 'track_observation_click'),
	url(r'^(?P<observation_id>\d+)/info$', 'get_observation_info'),
	url(r'^(?P<patient_id>\d+)/(?P<value_id>\d+)/individual_data_info$', 'get_individual_data_info'),
    url(r'^(?P<patient_id>\d+)/get_datas$', 'get_datas'),
    url(r'^(?P<patient_id>\d+)/add_new_data_type$', 'add_new_data_type'),
    url(r'^(?P<patient_id>\d+)/(?P<observation_id>\d+)/save_data_type$', 'save_data_type'),
    url(r'^(?P<patient_id>\d+)/(?P<observation_id>\d+)/delete_data$', 'delete_data'),
    url(r'^updateOrder$', 'update_order'),
    url(r'^(?P<observation_id>\d+)/get_pins$', 'get_pins'),
    url(r'^(?P<patient_id>\d+)/pin_to_problem$', 'obseration_pin_to_problem'),
    url(r'^(?P<patient_id>\d+)/(?P<component_id>\d+)/add_new_data$', 'add_new_data'),
    url(r'^(?P<patient_id>\d+)/(?P<value_id>\d+)/delete_individual_data$', 'delete_individual_data'),
    url(r'^(?P<patient_id>\d+)/(?P<value_id>\d+)/save_data$', 'save_data'),
)
