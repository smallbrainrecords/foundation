from rest_framework import serializers

from emr.models import MyStoryTab, MyStoryTextComponent, MyStoryTextComponentEntry

from users_app.serializers import SafeUserSerializer, UserProfileSerializer


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
            'datetime',
            )


class MyStoryTextComponentSerializer(serializers.ModelSerializer):

    patient = SafeUserSerializer()
    author = SafeUserSerializer()

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
