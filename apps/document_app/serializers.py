from rest_framework import serializers
from emr.models import Document
from users_app.serializers import SafeUserSerializer, UserProfileSerializer


class DocumentSerialization(serializers.ModelSerializer):
    author = UserProfileSerializer()
    patient = UserProfileSerializer()

    class Meta:
        model = Document
        fields = (
            'id',
            'author',
            'patient',
            'document',
            'created_on'
        )
