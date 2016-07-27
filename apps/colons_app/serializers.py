from rest_framework import serializers

from emr.models import ColonCancerScreening, ColonCancerStudy

from users_app.serializers import SafeUserSerializer, UserProfileSerializer
from todo_app.serializers import TodoSerializer
from problems_app.serializers import ProblemSerializer

class ColonCancerStudySerializer(serializers.ModelSerializer):
    author = UserProfileSerializer()

    class Meta:
        model = ColonCancerStudy
        fields = (
            'id',
            'author',
            'created_on',
            'finding',
            'result',
            'note',
            'study_date',
            'last_updated_date',
            'last_updated_user',
            )


class ColonCancerScreeningSerializer(serializers.ModelSerializer):
    patient = UserProfileSerializer()
    problem = ProblemSerializer()
    colon_studies = ColonCancerStudySerializer(many=True, read_only=True)

    class Meta:
        model = ColonCancerScreening
        fields = (
            'id',
            'patient',
            'problem',
            'created_on',
            'patient_refused',
            'colon_studies',
            )