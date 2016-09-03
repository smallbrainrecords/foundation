from django.conf.urls import patterns, include, url


urlpatterns = patterns('my_story_app.views',

    url(r'^(?P<patient_id>\d+)/get_my_story$', 'get_my_story'),
    url(r'^(?P<tab_id>\d+)/info$', 'get_tab_info'),
    url(r'^(?P<patient_id>\d+)/add_tab$', 'add_tab'),
    url(r'^(?P<patient_id>\d+)/(?P<tab_id>\d+)/add_text$', 'add_text'),
    url(r'^(?P<patient_id>\d+)/delete_tab/(?P<tab_id>\d+)$', 'delete_tab'),
    url(r'^(?P<patient_id>\d+)/save_tab/(?P<tab_id>\d+)$', 'save_tab'),
    url(r'^(?P<patient_id>\d+)/delete_text_component/(?P<component_id>\d+)$', 'delete_text_component'),
    url(r'^(?P<patient_id>\d+)/save_text_component/(?P<component_id>\d+)$', 'save_text_component'),
)
