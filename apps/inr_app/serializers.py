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
from datetime import datetime

from emr.models import (
    InrTextNote,
    ObservationComponent,
    ObservationPinToProblem,
    ObservationValue,
    Problem,
    UserProfile,
)
from rest_framework import serializers
from users_app.serializers import SafeUserSerializer


class InrTextNoteSerializer(serializers.ModelSerializer):
    author = SafeUserSerializer()
    patient = SafeUserSerializer()

    class Meta:
        model = InrTextNote
        fields = (
            'id',
            'author',
            'note',
            'datetime',
            'patient',
        )


class ProblemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Problem
        fields = (
            'problem_name',
        )


class InrSerializer(serializers.ModelSerializer):
    date_measured = serializers.SerializerMethodField()
    current_dose = serializers.SerializerMethodField()
    inr_value = serializers.SerializerMethodField()
    new_dosage = serializers.SerializerMethodField()
    next_inr = serializers.SerializerMethodField()

    class Meta:
        model = ObservationValue

        fields = (
            'id',
            'date_measured',
            'current_dose',
            'inr_value',
            'new_dosage',
            'next_inr'
        )

    def get_date_measured(self, obj):
        """

        :param obj:
        :return:
        """
        return obj.effective_datetime.strftime('%m/%d/%Y')

    def get_current_dose(self, obj):
        """
        :param obj:
        :return:
        """
        if hasattr(obj, 'inr') and obj.inr is not None:
            return obj.inr.current_dose
        else:
            return 0

    def get_inr_value(self, obj):
        if obj.value_quantity is not None:
            return "%g" % obj.value_quantity

    def get_new_dosage(self, obj):
        if hasattr(obj, 'inr') and obj.inr is not None:
            return obj.inr.new_dosage
        else:
            return 0

    def get_next_inr(self, obj):
        if hasattr(obj, 'inr') and obj.inr is not None:
            return obj.inr.next_inr.strftime('%m/%d/%Y')
        else:
            return datetime.today().strftime('%m/%d/%Y')


class INRPatientSerializer(serializers.ModelSerializer):
    """

    """
    avatar = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    date_of_birth = serializers.DateTimeField(format='%m/%d/%Y')
    problem_id = serializers.SerializerMethodField()
    user = SafeUserSerializer(many=False)

    class Meta:
        model = UserProfile
        fields = (
            'id',
            'avatar',
            'user',
            'full_name',
            'date_of_birth',
            'problem_id'
        )

    def get_avatar(self, obj):
        if hasattr(obj.portrait_image, 'path'):
            return obj.portrait_image.url

    def get_full_name(self, obj):
        return str(obj)

    def get_problem_id(self, obj):
        # Find patient's observation (INR data type)
        observation = ObservationComponent.objects.filter(component_code='6301-6').filter(
            observation__subject_id=obj.user_id).first()

        # Find all problem which is pinned to INR data
        if observation is not None and hasattr(observation, 'observation'):
            observation_pin_to_problem = ObservationPinToProblem.objects.filter(
                observation_id=observation.observation_id).first()

            if observation_pin_to_problem is not None:
                return observation_pin_to_problem.problem.id
