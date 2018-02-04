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

from emr.models import Observation, ObservationComponent, ObservationValueTextNote, ObservationPinToProblem, \
    ObservationUnit, ObservationValue
from users_app.serializers import SafeUserSerializer


class ObservationValueTextNoteSerializer(serializers.ModelSerializer):
    author = SafeUserSerializer()

    class Meta:
        model = ObservationValueTextNote
        fields = (
            'id',
            'author',
            'note',
            'datetime',
        )


class ObservationUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = ObservationUnit
        fields = (
            'id',
            'observation',
            'value_unit',
            'is_used',
        )


class ObservationValueSerializer(serializers.ModelSerializer):
    author = SafeUserSerializer()
    date = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    observation = serializers.SerializerMethodField()
    value_quantity = serializers.SerializerMethodField()
    observation_value_notes = ObservationValueTextNoteSerializer(many=True, read_only=True)

    class Meta:
        model = ObservationValue
        fields = (
            'id',
            'component',
            'author',
            'value_quantity',
            'effective_datetime',
            'created_on',
            'date',
            'time',
            'observation',
            'observation_value_notes',
        )

    def get_date(self, obj):
        if not obj.effective_datetime:
            return ''
        return obj.effective_datetime.strftime('%m/%d/%Y')

    def get_time(self, obj):
        if not obj.effective_datetime:
            return ''
        return obj.effective_datetime.strftime('%H:%M')

    def get_observation(self, obj):
        return obj.component.observation.id

    def get_value_quantity(self, obj):
        if obj.value_quantity is not None:
            return "%g" % float(obj.value_quantity)
        else:
            return 0


class ObservationComponentSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    author = SafeUserSerializer()
    observation_component_values = ObservationValueSerializer(many=True, read_only=True)

    class Meta:
        model = ObservationComponent
        fields = (
            'id',
            'name',
            'value_quantity',
            'effective_datetime',
            'created_on',
            'author',
            'observation',
            'date',
            'time',
            'observation_component_values',
            'component_code',
        )

    def get_date(self, obj):
        if not obj.effective_datetime:
            return ''
        return obj.effective_datetime.strftime('%m/%d/%Y')

    def get_time(self, obj):
        if not obj.effective_datetime:
            return ''
        return obj.effective_datetime.strftime('%H:%M')


class ObservationSerializer(serializers.ModelSerializer):
    subject = SafeUserSerializer()
    encounter = SafeUserSerializer()
    performer = SafeUserSerializer()
    author = SafeUserSerializer()
    observation_components = ObservationComponentSerializer(many=True, read_only=True)
    observation_units = ObservationUnitSerializer(many=True, read_only=True)

    class Meta:
        model = Observation
        fields = (
            'id',
            'name',
            'status',
            'category',
            'code',
            'subject',
            'encounter',
            'performer',
            'author',
            'effective_datetime',
            'comments',
            'created_on',
            'observation_components',
            'observation_units',
            'color',
            'graph',
        )


class ObservationPinToProblemSerializer(serializers.ModelSerializer):
    author = SafeUserSerializer()

    class Meta:
        model = ObservationPinToProblem
        fields = (
            'id',
            'author',
            'observation',
            'problem',
        )
