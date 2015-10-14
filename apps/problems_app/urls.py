from django.conf.urls import patterns, url


urlpatterns = patterns(
    'problems_app.views',

    url(r'^problem/(?P<problem_id>\d+)/info$',
        'get_problem_info'),
    url(r'^problem/(?P<problem_id>\d+)/activity/$',
        'get_problem_activity'),
    url(r'^problem/(?P<problem_id>\d+)/track/click/$',
        'track_problem_click'),

    url(r'^patient/(?P<patient_id>\d+)/problems/add/new_problem$',
        'add_patient_problem'),

    url(r'^problem/(?P<problem_id>\d+)/update_status$',
        'update_problem_status'),

    url(r'^problem/(?P<problem_id>\d+)/update_start_date$',
        'update_start_date'),

    url(r'^problem/(?P<problem_id>\d+)/add_wiki_note$',
        'add_wiki_note'),

    url(r'^problem/(?P<problem_id>\d+)/add_history_note$',
        'add_history_note'),

    url(r'^problem/(?P<problem_id>\d+)/add_goal$',
        'add_problem_goal'),

    url(r'^problem/(?P<problem_id>\d+)/add_todo$',
        'add_problem_todo'),

    url(r'^problem/(?P<problem_id>\d+)/upload_image$',
        'upload_problem_image'),

    url(r'^problem/(?P<problem_id>\d+)/image/(?P<image_id>\d+)/delete/$',
        'delete_problem_image'),

    url(r'^problem/relate/$', 'relate_problem'), )
