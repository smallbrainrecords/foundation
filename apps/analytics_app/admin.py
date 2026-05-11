from django.contrib import admin
from .models import UserEvent


@admin.register(UserEvent)
class UserEventAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'entity_type', 'patient_session_id', 'app_version')
    list_filter = ('action', 'entity_type', 'event_schema_version', 'app_version')
    search_fields = ('action', 'entity_type', 'entity_id', 'patient_session_id')
    date_hierarchy = 'timestamp'
    readonly_fields = ('server_timestamp',)
    raw_id_fields = ('user',)
