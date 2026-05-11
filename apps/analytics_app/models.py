from django.conf import settings
from django.db import models


class UserEvent(models.Model):
    timestamp = models.DateTimeField(db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='analytics_events',
    )
    action = models.CharField(max_length=100, db_index=True)
    entity_type = models.CharField(max_length=50, blank=True, null=True)
    entity_id = models.CharField(max_length=100, blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)
    patient_session_id = models.CharField(max_length=36, db_index=True)
    sequence = models.BigIntegerField()
    event_schema_version = models.IntegerField(default=1)
    app_version = models.CharField(max_length=20)
    server_timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['patient_session_id', 'sequence']),
        ]

    def __str__(self):
        return f"{self.user} — {self.action} @ {self.timestamp}"
