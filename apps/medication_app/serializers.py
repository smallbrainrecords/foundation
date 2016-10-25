from rest_framework import serializers

from emr.models import Inr, InrValue, Medication, MedicationTextNote, MedicationPinToProblem, InrTextNote

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
    patient = UserProfileSerializer()
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
            'current_dose',
            'new_dosage',
            'next_inr',
            'created_on',
            )


class InrTextNote(serializers.ModelSerializer):
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


class InrSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer()
    patient = UserProfileSerializer()
    inr_values = InrValueSerializer(many=True, read_only=True)
    inr_notes = InrTextNote(many=True, read_only=True)

    class Meta:
        model = Inr

        fields = (
            'id',
            'author',
            'patient',
            'pin',
            'created_on',
            'inr_values',
            'inr_notes',
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