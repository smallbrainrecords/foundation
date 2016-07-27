from django.conf.urls import patterns, include, url


urlpatterns = patterns('colons_app.views',

    url(r'^(?P<colon_id>\d+)/info$', 'get_colon_info'),
    url(r'^study/(?P<study_id>\d+)/info$', 'get_study_info'),
    url(r'^(?P<colon_id>\d+)/add_study$', 'add_study'),
    url(r'^(?P<study_id>\d+)/delete_study$', 'delete_study'),
    url(r'^(?P<study_id>\d+)/edit_study$', 'edit_study'),
)
