from datetime import datetime

from rest_framework import serializers

from emr.models import InrTextNote, Problem, ObservationValue
from users_app.serializers import UserProfileSerializer


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
        TODO: What is self
        :param obj:
        :return:
        """
        if hasattr(obj, 'inr') and obj.inr is not None:
            return obj.inr.current_dose
        else:
            return 0

    def get_inr_value(self, obj):
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
