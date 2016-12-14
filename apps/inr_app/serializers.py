from rest_framework import serializers

from emr.models import Inr, InrTextNote, Problem
from data_app.serializers import ObservationValueSerializer
from todo_app.serializers import TodoSerializer
from users_app.serializers import UserProfileSerializer


# class InrValueSerializer(serializers.ModelSerializer):
#     author = UserProfileSerializer()
#
#     class Meta:
#         model = InrValue
#
#         fields = (
#             'id',
#             'inr',
#             'author',
#             'value',
#             'effective_datetime',
#             'current_dose',
#             'new_dosage',
#             'next_inr',
#             'ispatient',
#             'created_on',
#         )


class InrTextNoteSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer()
    patient = UserProfileSerializer()

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
    # author = UserProfileSerializer()

    class Meta:
        model = Problem
        fields = (
            'problem_name',
        )


# class InrValueSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Problem
#         fields = (
#             'id',
#             'value',
#             'effective_datetime',
#             'current_dose',
#             'new_dosage',
#             'next_inr',
#             )

class InrSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer()
    observation_value = ObservationValueSerializer()

    class Meta:
        model = Inr

        fields = (
            'id',
            'author',
            'observation_value',
            'current_dose',
            'new_dosage',
            'next_inr',
            'created_on',
        )
