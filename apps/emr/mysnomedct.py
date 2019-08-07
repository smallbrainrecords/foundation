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

from emr.models import VWProblems, VWMedications


class VWMedicationsSerializers(serializers.ModelSerializer):
    concept_id = serializers.CharField(source='conceptid')
    name = serializers.CharField(source='term')

    class Meta:
        model = VWMedications
        fields = ('concept_id', 'name')


class VWProblemsSerializers(serializers.ModelSerializer):
    code = serializers.CharField(source='conceptid')

    class Meta:
        model = VWProblems
        fields = ('code', 'term')
