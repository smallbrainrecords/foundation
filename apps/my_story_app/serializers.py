from rest_framework import serializers

from emr.models import MyStoryTab, MyStoryTextComponent, MyStoryTextComponentEntry

from users_app.serializers import SafeUserSerializer, UserProfileSerializer


class MyStoryTextComponentEntrySerializer(serializers.ModelSerializer):
    author = SafeUserSerializer()

    class Meta:
        model = MyStoryTextComponentEntry
        fields = (
            'id',
            'author',
            'component',
            'text',
            'datetime',
            'private',
            )


class MyStoryTextComponentSerializer(serializers.ModelSerializer):

    patient = SafeUserSerializer()
    author = SafeUserSerializer()
    last_updated_user = SafeUserSerializer()
    text_component_entries = MyStoryTextComponentEntrySerializer(many=True, read_only=True)

    class Meta:
        model = MyStoryTextComponent

        fields = (
            'id',
            'patient',
            'author',
            'tab',
            'name',
            'text',
            'datetime',
            'last_updated_user',
            'last_updated_date',
            'concept_id',
            'private',
            'text_component_entries',
            'is_all',
            )


class MyStoryTabSerializer(serializers.ModelSerializer):

    patient = SafeUserSerializer()
    author = SafeUserSerializer()

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
            )
