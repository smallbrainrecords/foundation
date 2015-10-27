from rest_framework import serializers
from .models import TextNote
from users_app.serializers import UserProfileSerializer


class TextNoteSerializer(serializers.ModelSerializer):

    author = UserProfileSerializer()

    class Meta:
        model = TextNote
        fields = (
            'id',
            'author',
            'by',
            'note',
            'datetime')
