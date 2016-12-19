from django.conf.urls import patterns, include, url

urlpatterns = patterns('inr_app.views',
                       url(r'^(?P<patient_id>\d+)/target/get$', 'get_inr_target'),
                       url(r'^(?P<patient_id>\d+)/target/get$', 'get_inr_target'),
                       url(r'^(?P<patient_id>\d+)/target/set$', 'set_inr_target'),
                       url(r'^(?P<patient_id>\d+)/inrs', 'get_inr_table'),
                       url(r'^(?P<patient_id>\d+)/inr/add', 'add_inr'),
                       url(r'^(?P<patient_id>\d+)/inr/update', 'update_inr'),
                       url(r'^(?P<patient_id>\d+)/inr/delete', 'delete_inr'),
                       url(r'^(?P<patient_id>\d+)/problems', 'get_problems'),
                       url(r'^(?P<patient_id>\d+)/medications', 'get_medications'),
                       url(r'^(?P<patient_id>\d+)/orders', 'get_orders'),
                       url(r'^(?P<patient_id>\d+)/order/add', 'add_order'),
                       url(r'^(?P<patient_id>\d+)/notes', 'get_inr_note'),
                       url(r'^(?P<patient_id>\d+)/note/add', 'add_note'),
                       url(r'^patients', 'find_patient')
                       )
