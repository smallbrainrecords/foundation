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

from emr.models import MyStoryTab, MyStoryTextComponent, MyStoryTextComponentEntry
from users_app.serializers import SafeUserSerializer


class MyStoryTextComponentEntrySerializer(serializers.ModelSerializer):
    author = SafeUserSerializer()

    class Meta:
        model = MyStoryTextComponentEntry
        fields = (
            'id',
            'patient',
            'author',
            'component',
            'text',
            'datetime'
        )


class MyStoryTextComponentSerializer(serializers.ModelSerializer):
    patient = SafeUserSerializer()
    author = SafeUserSerializer()
    text_component_entries = MyStoryTextComponentEntrySerializer(many=True)

    class Meta:
        model = MyStoryTextComponent

        fields = (
            'id',
            'patient',
            'author',
            'tab',
            'name',
            'datetime',
            'concept_id',
            'private',
            'is_all',
            'text_component_entries'
        )


class MyStoryTabSerializer(serializers.ModelSerializer):
    patient = SafeUserSerializer()
    author = SafeUserSerializer()
    my_story_tab_components = MyStoryTextComponentSerializer(many=True)

    class Meta:
        model = MyStoryTab

        fields = (
            'id',
            'patient',
            'author',
            'name',
            'datetime',
            'private',
            'is_all',
            'my_story_tab_components'
        )
