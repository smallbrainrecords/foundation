from rest_framework import serializers

from emr.models import ColonCancerScreening, ColonCancerStudy, ColonCancerStudyImage, RiskFactor

from users_app.serializers import SafeUserSerializer, UserProfileSerializer
from todo_app.serializers import TodoSerializer
from problems_app.serializers import ProblemSerializer


class StudyImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = ColonCancerStudyImage

        fields = (
            'id',
            'author',
            'study',
            'image',
            'datetime')


class ColonCancerStudySerializer(serializers.ModelSerializer):
    author = UserProfileSerializer()
    last_updated_user = UserProfileSerializer()
    study_images = StudyImageSerializer(many=True, read_only=True)

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
            'study_images',
            )


class RiskFactorSerializer(serializers.ModelSerializer):

    class Meta:
        model = RiskFactor

        fields = (
            'id',
            'colon',
            'factor')


class ColonCancerScreeningSerializer(serializers.ModelSerializer):
    patient = UserProfileSerializer()
    problem = ProblemSerializer()
    colon_studies = ColonCancerStudySerializer(many=True, read_only=True)
    colon_risk_factors = RiskFactorSerializer(many=True, read_only=True)
    last_risk_updated_user = UserProfileSerializer()

    class Meta:
        model = ColonCancerScreening
        fields = (
            'id',
            'patient',
            'problem',
            'created_on',
            'patient_refused',
            'colon_studies',
            'risk',
            'colon_risk_factors',
            'last_risk_updated_date',
            'last_risk_updated_user',
            )