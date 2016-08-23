from django.conf.urls import patterns, include, url


urlpatterns = patterns('my_story_app.views',

    url(r'^(?P<patient_id>\d+)/get_my_story$', 'get_my_story'),
    url(r'^(?P<tab_id>\d+)/info$', 'get_tab_info'),
    url(r'^(?P<patient_id>\d+)/add_tab$', 'add_tab'),
)
