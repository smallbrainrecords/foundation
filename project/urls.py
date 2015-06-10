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

    url(r'^patient/manage/(?P<user_id>\d+)/$', 'emr.views.manage_patient'),

    url(r'^get_problems/(?P<patient_id>\d+)/$', 'emr.views.get_patient_data'),
    url(r'^change_status/$', 'emr.views.change_status'),
    url(r'^patient/(?P<patient_id>\d+)/add_problem/$', 'emr.views.add_problem'),
    url(r'^add_patient_summary/(?P<patient_id>\d+)/$', 'emr.views.save_patient_summary'),
    url(r'^list_terms/$', 'emr.views.list_snomed_terms'),
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

    url(r'^patient/(?P<patient_id>\d+)/info$', 'emr.views.get_patient_info'),
    url(r'^problem/(?P<problem_id>\d+)/info$', 'emr.views.get_problem_info'),
    url(r'^goal/(?P<goal_id>\d+)/info$', 'emr.views.get_goal_info'),
    url(r'^encounter/(?P<encounter_id>\d+)/info$', 'emr.views.get_encounter_info'),

    url(r'^patient/(?P<patient_id>\d+)/encounter/status$', 'emr.views.patient_encounter_status'),

    url(r'^patient/(?P<patient_id>\d+)/encounter/start$', 'emr.views.create_new_encounter'),

    url(r'^encounter/(?P<encounter_id>\d+)/stop$', 'emr.views.stop_patient_encounter'),

    url(r'^encounter/add/event_summary$', 'emr.views.add_event_summary'),

    url(r'^patient/(?P<patient_id>\d+)/pain_avatars$', 'pain.views.patient_pain_avatars'),

    url(r'^patient/(?P<patient_id>\d+)/goals/add/new_goal$', 'emr.views.add_patient_goal'),

    url(r'^patient/(?P<patient_id>\d+)/todos/add/new_todo$', 'emr.views.add_patient_todo'),

    url(r'^patient/(?P<patient_id>\d+)/profile/update_summary$', 'emr.views.update_patient_summary'),


    url(r'^patient/(?P<patient_id>\d+)/pain/add_pain_avatar$', 'pain.views.add_pain_avatar'),

    url(r'^patient/(?P<patient_id>\d+)/problem/(?P<problem_id>\d+)/update_status$', 'emr.views.update_problem_status'),

    url(r'^patient/(?P<patient_id>\d+)/problem/(?P<problem_id>\d+)/update_start_date$', 'emr.views.update_start_date'),

    url(r'^patient/(?P<patient_id>\d+)/problem/(?P<problem_id>\d+)/add_patient_note$', 'emr.views.add_patient_note'),

    url(r'^patient/(?P<patient_id>\d+)/problem/(?P<problem_id>\d+)/add_physician_note$', 'emr.views.add_physician_note'),

    url(r'^patient/(?P<patient_id>\d+)/problem/(?P<problem_id>\d+)/add_goal$', 'emr.views.add_problem_goal'),

    url(r'^patient/(?P<patient_id>\d+)/problem/(?P<problem_id>\d+)/add_todo$', 'emr.views.add_problem_todo'),


    url(r'^patient/(?P<patient_id>\d+)/goal/(?P<goal_id>\d+)/add_note$', 'emr.views.add_goal_note'),

    url(r'^patient/(?P<patient_id>\d+)/goal/(?P<goal_id>\d+)/update_status$', 'emr.views.update_goal_status'),

    url(r'^patient/(?P<patient_id>\d+)/problem/(?P<problem_id>\d+)/upload_image$', 'emr.views.upload_problem_image'),

    url(r'^problem/(?P<problem_id>\d+)/image/(?P<image_id>\d+)/delete/$', 'emr.views.delete_problem_image'),

)
