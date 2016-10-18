
from rest_framework import serializers

from emr.models import UserProfile
from django.contrib.auth.models import User


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
			)
