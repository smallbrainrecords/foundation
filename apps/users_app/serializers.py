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

from django.contrib.auth.models import User
from rest_framework import serializers

from emr.models import UserProfile


class SafeUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile

        fields = (
            'id',
            'user',
            'role',
        )


class SafeUserSerializer(serializers.ModelSerializer):
    profile = SafeUserProfileSerializer(many=False)

    class Meta:
        model = User

        fields = (
            'id',
            'first_name',
            'last_name',
            'username',
            'email',
            'profile',
            'is_active',
        )


class UserProfileSerializer(serializers.ModelSerializer):
    user = SafeUserSerializer()
    deceased_date = serializers.DateTimeField(format='%m/%d/%Y')
    date_of_birth = serializers.DateTimeField(format='%m/%d/%Y')

    class Meta:
        model = UserProfile

        fields = (
            'id',
            'user',
            'role',
            'data',
            'cover_image',
            'portrait_image',
            'summary',
            'sex',
            'date_of_birth',
            'phone_number',
            'note',
            'active_reason',
            'deceased_date',
            'last_access_tagged_todo',
            'insurance_medicare',
            'insurance_note'
        )


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(many=False)

    class Meta:
        model = User

        fields = (
            'id',
            'first_name',
            'last_name',
            'username',
            'email',
            'is_active',
            'profile',
        )

