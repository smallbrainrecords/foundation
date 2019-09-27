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

from data_app.serializers import ObservationSerializer
from emr.models import AOneCTextNote, AOneC
from problems_app.serializers import ProblemSerializer
from todo_app.serializers import TodoSerializer
from users_app.serializers import SafeUserSerializer


class AOneCTextNoteSerializer(serializers.ModelSerializer):
    author = SafeUserSerializer()

    class Meta:
        model = AOneCTextNote
        fields = (
            'id',
            'author',
            'note',
            'datetime',
        )


class AOneCSerializer(serializers.ModelSerializer):
    problem = ProblemSerializer()
    observation = ObservationSerializer()
    a1c_todos = TodoSerializer(many=True, read_only=True)
    a1c_notes = AOneCTextNoteSerializer(many=True, read_only=True)

    class Meta:
        model = AOneC
        fields = (
            'id',
            'problem',
            'observation',
            'todo_past_six_months',
            'patient_refused_A1C',
            'a1c_todos',
            'a1c_notes',
        )
