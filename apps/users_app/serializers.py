
from rest_framework import serializers

from emr.models import UserProfile
from django.contrib.auth.models import User



class SafeUserSerializer(serializers.ModelSerializer):

	class Meta:
		model = User

		fields = (
				'id',
				'first_name',
				'last_name',
				'username',
				'email',
			)



class UserProfileSerializer(serializers.ModelSerializer):

	user = SafeUserSerializer()

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
			)