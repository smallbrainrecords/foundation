from django.conf.urls import patterns, include, url


urlpatterns = patterns('problems_app.views',

    url(r'^problem/(?P<problem_id>\d+)/info$', 'get_problem_info'),
    url(r'^problem/(?P<problem_id>\d+)/track/click/$', 'track_problem_click'),
    
    url(r'^patient/(?P<patient_id>\d+)/problems/add/new_problem$', 'add_patient_problem'),

    url(r'^patient/(?P<patient_id>\d+)/problem/(?P<problem_id>\d+)/update_status$', 'update_problem_status'),
    url(r'^patient/(?P<patient_id>\d+)/problem/(?P<problem_id>\d+)/update_start_date$', 'update_start_date'),
    url(r'^patient/(?P<patient_id>\d+)/problem/(?P<problem_id>\d+)/add_patient_note$', 'add_patient_note'),
    url(r'^patient/(?P<patient_id>\d+)/problem/(?P<problem_id>\d+)/add_physician_note$', 'add_physician_note'),
    url(r'^patient/(?P<patient_id>\d+)/problem/(?P<problem_id>\d+)/add_goal$', 'add_problem_goal'),
    url(r'^patient/(?P<patient_id>\d+)/problem/(?P<problem_id>\d+)/add_todo$', 'add_problem_todo'),

    url(r'^patient/(?P<patient_id>\d+)/problem/(?P<problem_id>\d+)/upload_image$', 'upload_problem_image'),
    url(r'^problem/(?P<problem_id>\d+)/image/(?P<image_id>\d+)/delete/$', 'delete_problem_image'),



	)
