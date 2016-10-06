from rest_framework import serializers

from emr.models import Inr, InrValue, Medication, MedicationTextNote, MedicationPinToProblem

from users_app.serializers import SafeUserSerializer, UserProfileSerializer


class MedicationTextNoteSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer()

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
    author = UserProfileSerializer()
    medication_notes = MedicationTextNoteSerializer(many=True, read_only=True)

    class Meta:
        model = Medication

        fields = (
            'id',
            'author',
            'medication_notes',
            'inr',
            'name',
            'concept_id',
            'current',
            'created_on',
            )


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
            'created_on',
            )


class InrSerializer(serializers.ModelSerializer):
    patient = SafeUserSerializer()
    inr_values = InrValueSerializer(many=True, read_only=True)
    inr_medications = MedicationSerializer(many=True, read_only=True)

    class Meta:
        model = Inr

        fields = (
            'id',
            'patient',
            'note',
            'created_on',
            'inr_values',
            'inr_medications',
            )


class MedicationPinToProblemSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer()
    medication = MedicationSerializer()

    class Meta:
        model = MedicationPinToProblem
        fields = (
            'id',
            'author',
            'medication',
            'problem',
            )