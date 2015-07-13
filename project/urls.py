from django.conf.urls import patterns, include, url
from emr.views import AuthComplete, LoginError
from django.views.generic import TemplateView
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()
import settings

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'emr.views.home', name='home'),
    # url(r'^emr/', include('emr.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    url(r'^project/admin/', include('project_admin_app.urls')),

    url('^pain/create_pain_avatar/(?P<patient_id>\d+)/$', 'pain.views.create_pain_avatar'),
    url('^pain/reset/$', 'pain.views.reset'),
    url(r'^login-error/$', LoginError.as_view()),
    url(r'', include('social_auth.urls')),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/login/'}),
    #url(r'^login/$', TemplateView.as_view(template_name='login.html')),
    url(r'^login/$', 'emr.views.login_user'),
    url(r'^register/$', 'emr.views.register'),
    url(r'^list_of_unregistered_users/$', 'emr.views.list_of_unregistered_users'),
    url(r'^register_users/$', 'emr.views.register_users'),
    url(r'^list_of_users/$', 'emr.views.list_users'),
    url(r'^patient/(?P<user_id>\d+)/$', 'emr.views.view_patient'),
    url(r'^get_problems/(?P<patient_id>\d+)/$', 'emr.views.get_patient_data'),
    url(r'^change_status/$', 'emr.views.change_status'),
    url(r'^patient/(?P<patient_id>\d+)/add_problem/$', 'emr.views.add_problem'),
    url(r'^add_patient_summary/(?P<patient_id>\d+)/$', 'emr.views.save_patient_summary'),
    
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT, 'show_indexes': True}),
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '/home/tim/core/static', 'show_indexes': True}),
    url(r'^upload_image_to_problem/(?P<problem_id>\d+)/$', 'emr.views.upload_image_to_problem'),
    url(r'^submit_data_for_problem/(?P<problem_id>\d+)/$', 'emr.views.submit_data_for_problem'),
    url(r'^update/$', 'emr.views.update'),
    url(r'^create_encounter/(?P<patient_id>\d+)/$', 'emr.views.create_encounter'),
    url(r'^stop_encounter/(?P<encounter_id>\d+)/$', 'emr.views.stop_encounter'),
    url(r'^save_encounter_event/$', 'emr.views.save_event_summary'),
    url(r'^encounter/(?P<encounter_id>\d+)/$', 'emr.views.encounter'),


    # New URLS
    url(r'^list_terms/$', 'emr.views.list_snomed_terms'),

    # Users
    url(r'^u/', include('users_app.urls')),


    # Problems 
    url(r'^p/', include('problems_app.urls')),



    # Goals
    url(r'^g/', include('goals_app.urls')),



    # Encounters
    url(r'^enc/', include('encounters_app.urls')),

    # Todos
    url(r'^todo/', include('todo_app.urls')),

    # Pain Avatars
    url(r'^patient/(?P<patient_id>\d+)/pain_avatars$', 'pain.views.patient_pain_avatars'),
    url(r'^patient/(?P<patient_id>\d+)/pain/add_pain_avatar$', 'pain.views.add_pain_avatar'),

)
