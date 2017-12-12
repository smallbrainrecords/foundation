from rest_framework import serializers

from emr.models import Medication, MedicationTextNote, MedicationPinToProblem
from users_app.serializers import SafeUserSerializer


class MedicationTextNoteSerializer(serializers.ModelSerializer):
    author = SafeUserSerializer()

    class Meta:
        model = MedicationTextNote
        fields = (
            'id',
            'author',
            'note',
            'medication',
            'datetime',
            )


class MedicationSerializer(serializers.ModelSerializer):
    author = SafeUserSerializer()
    patient = SafeUserSerializer()
    medication_notes = MedicationTextNoteSerializer(many=True, read_only=True)

    class Meta:
        model = Medication

        fields = (
            'id',
            'author',
            'patient',
            'medication_notes',
            'name',
            'concept_id',
            'current',
            'search_str',
            'created_on',
            )


class MedicationPinToProblemSerializer(serializers.ModelSerializer):
    author = SafeUserSerializer()
    medication = MedicationSerializer()

    class Meta:
        model = MedicationPinToProblem
        fields = (
            'id',
            'author',
            'medication',
            'problem',
            )