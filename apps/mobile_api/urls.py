from django.urls import re_path as url
from . import views

urlpatterns = [
    url(r'^login/$', views.mobile_login),
    url(r'^change-password/$', views.mobile_change_password),
    url(r'^staff-set-password/$', views.mobile_staff_set_password),
    url(r'^toggle-patient-active/$', views.mobile_toggle_patient_active),
    url(r'^patients/$', views.mobile_patients),
    url(r'^team/$', views.mobile_team),
    url(r'^team/assignments/$', views.mobile_team_assignments),
    url(r'^team/assign/$', views.mobile_team_assign),
    url(r'^team/unassign/$', views.mobile_team_unassign),
    url(r'^patient/(?P<patient_id>\d+)/full$', views.mobile_patient_full),
    url(r'^media/encounter/(?P<encounter_id>\d+)/audio$', views.mobile_encounter_audio),
    url(r'^media/document/(?P<document_id>\d+)/file$', views.mobile_document_file),
    url(r'^media/image/(?P<image_id>\d+)$', views.mobile_image_file),
    url(r'^patient/(?P<patient_id>\d+)/encounter/upload-audio$', views.mobile_upload_encounter_audio),
    url(r'^patient/(?P<patient_id>\d+)/encounter$', views.mobile_create_encounter),
    url(r'^patient/(?P<patient_id>\d+)/encounter/(?P<encounter_id>\d+)$', views.mobile_update_encounter),
    url(r'^patient/(?P<patient_id>\d+)/document/upload$', views.mobile_upload_document),
    # Problem images (PR-2)
    url(r'^patient/(?P<patient_id>\d+)/problem/(?P<problem_id>\d+)/image$', views.mobile_upload_problem_image),
    url(r'^patient/(?P<patient_id>\d+)/image/(?P<image_id>\d+)$', views.mobile_delete_problem_image),
    url(r'^patient/(?P<patient_id>\d+)/my-story/(?P<component_id>\d+)/entry$', views.mobile_save_my_story_entry),
    # Problem CRUD
    url(r'^patient/(?P<patient_id>\d+)/problem$', views.mobile_create_problem),
    url(r'^patient/(?P<patient_id>\d+)/problem/(?P<problem_id>\d+)$', views.mobile_update_problem),
    url(r'^patient/(?P<patient_id>\d+)/problem/(?P<problem_id>\d+)/note$', views.mobile_create_problem_note),
    url(r'^patient/(?P<patient_id>\d+)/problem/(?P<problem_id>\d+)/note/(?P<note_id>\d+)$', views.mobile_update_problem_note),
    url(r'^patient/(?P<patient_id>\d+)/problem/(?P<problem_id>\d+)/label$', views.mobile_create_problem_label),
    url(r'^patient/(?P<patient_id>\d+)/problem/relationship$', views.mobile_create_problem_relationship),
    # Todo CRUD
    url(r'^patient/(?P<patient_id>\d+)/todo$', views.mobile_create_todo),
    url(r'^patient/(?P<patient_id>\d+)/todo/(?P<todo_id>\d+)$', views.mobile_update_todo),
    url(r'^patient/(?P<patient_id>\d+)/todo/(?P<todo_id>\d+)/comment$', views.mobile_create_todo_comment),
    url(r'^patient/(?P<patient_id>\d+)/todo/(?P<todo_id>\d+)/label$', views.mobile_create_todo_label),
    url(r'^patient/(?P<patient_id>\d+)/todo/(?P<todo_id>\d+)/member$', views.mobile_add_todo_member),
    url(r'^patient/(?P<patient_id>\d+)/todo/(?P<todo_id>\d+)/member/(?P<user_id>\d+)$', views.mobile_remove_todo_member),
    # Observation values
    url(r'^patient/(?P<patient_id>\d+)/observation/component/(?P<component_id>\d+)/value$', views.mobile_create_observation_value),
    url(r'^patient/(?P<patient_id>\d+)/observation/value/(?P<value_id>\d+)$', views.mobile_update_observation_value),
    # Observation parent (comments / "note") + pins
    url(r'^patient/(?P<patient_id>\d+)/observation/(?P<observation_id>\d+)$', views.mobile_update_observation),
    url(r'^patient/(?P<patient_id>\d+)/observation/(?P<observation_id>\d+)/pin/(?P<problem_id>\d+)$', views.mobile_observation_pin),
    # Label catalog
    url(r'^labels/$', views.mobile_create_label),
    url(r'^labels/(?P<label_id>\d+)$', views.mobile_update_label),
    # Tagged todos (cross-patient)
    url(r'^my-tagged-todos/$', views.mobile_my_tagged_todos),
    # Analytics
    url(r'^events/batch/$', views.mobile_batch_events),
    # Error reporting
    url(r'^errors/batch/$', views.mobile_batch_errors),
    # Terminology mapping
    url(r'^mapping/snomed-to-icd/$', views.get_snomed_to_icd10),
]
