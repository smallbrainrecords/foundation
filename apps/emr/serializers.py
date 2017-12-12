from rest_framework import serializers

from users_app.serializers import SafeUserSerializer
from .models import TextNote


class TextNoteSerializer(serializers.ModelSerializer):
    author = SafeUserSerializer()

    class Meta:
        model = TextNote
        fields = (
            'id',
            'author',
            'by',
            'note',
            'datetime')

