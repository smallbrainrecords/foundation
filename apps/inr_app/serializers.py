from rest_framework import serializers

from emr.models import Inr, InrValue, InrTextNote, Problem

from users_app.serializers import SafeUserSerializer, UserProfileSerializer
from todo_app.serializers import TodoSerializer


class InrValueSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer()

    class Meta:
        model = InrValue

        fields = (
            'id',
            'inr',
            'author',
            'value',
            'effective_datetime',
            'current_dose',
            'new_dosage',
            'next_inr',
            'ispatient',
            'created_on',
            )


class InrTextNoteSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer()

    class Meta:
        model = InrTextNote
        fields = (
            'id',
            'author',
            'note',
            'inr',
            'datetime',
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
    patient = UserProfileSerializer()
    inr_values = InrValueSerializer(many=True, read_only=True)
    inr_notes = InrTextNoteSerializer(many=True, read_only=True)
    inr_todos = TodoSerializer(many=True, read_only=True)
    class Meta:
        model = Inr

        fields = (
            'id',
            'author',
            'patient',
            'observation',
            'created_on',
            'inr_values',
            'inr_notes',
            'inr_todos',
            'target',
            )
