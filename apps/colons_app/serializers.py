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

from emr.models import ColonCancerScreening, ColonCancerStudy, ColonCancerStudyImage, RiskFactor, ColonCancerTextNote
from problems_app.serializers import ProblemSerializer
from todo_app.serializers import TodoSerializer
from users_app.serializers import SafeUserSerializer, UserSerializer


class ColonCancerTextNoteSerializer(serializers.ModelSerializer):
    author = SafeUserSerializer()

    class Meta:
        model = ColonCancerTextNote
        fields = (
            'id',
            'author',
            'note',
            'datetime',
        )


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
    author = SafeUserSerializer()
    last_updated_user = SafeUserSerializer()
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
    colon_studies = ColonCancerStudySerializer(many=True, read_only=True)
    colon_risk_factors = RiskFactorSerializer(many=True, read_only=True)
    colon_cancer_todos = TodoSerializer(many=True, read_only=True)
    colon_notes = ColonCancerTextNoteSerializer(many=True, read_only=True)
    problem = ProblemSerializer()
    patient = UserSerializer()
    last_risk_updated_user = SafeUserSerializer()

    class Meta:
        model = ColonCancerScreening
        fields = (
            'id',
            'patient',
            'problem',
            'created_on',
            'patient_refused',
            'not_appropriate',
            'colon_studies',
            'risk',
            'colon_risk_factors',
            'last_risk_updated_date',
            'last_risk_updated_user',
            'todo_past_five_years',
            'colon_cancer_todos',
            'patient_refused_on',
            'not_appropriate_on',
            'colon_notes',
        )
