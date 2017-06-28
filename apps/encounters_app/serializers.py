from rest_framework import serializers

from emr.models import Encounter, EncounterEvent


class EncounterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Encounter

        fields = (
            'id',
            'physician',
            'patient',
            'starttime',
            'stoptime',
            'audio',
            'audio_played_count',
            'recorder_status',
            'video',
            'note',
            'duration',
            'is_active')


class EncounterEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = EncounterEvent

        fields = (
            'id',
            'encounter',
            'datetime',
            'summary',
            'video_seconds',
            'video_timestamp',
            'timestamp',
            'is_favorite',
            'name_favorite',)
