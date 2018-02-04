"""
Copyright (c) Small Brain Records 2014-2018 Kevin Perdue, James Ryan with contributors Timothy Clemens and Dinh Ngoc Anh

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""
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
