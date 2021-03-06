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
from twisted.trial._synctest import Todo

from emr.models import UserProfile, Narrative, VWTopPatients, ToDo, Problem, ProblemNote, Goal, EncounterEvent, \
    Document, MyStoryTextComponent, MyStoryTab


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


class NarrativeSerializer(serializers.ModelSerializer):
    datetime = serializers.DateTimeField(source='created_at')
    author = serializers.StringRelatedField()

    class Meta:
        model = Narrative

        fields = (
            'id',
            'description',
            'author',
            'datetime'
        )


class TopPatientSerializer(serializers.ModelSerializer):
    todo = serializers.SerializerMethodField()
    problem = serializers.SerializerMethodField()
    document = serializers.SerializerMethodField()
    encounter = serializers.SerializerMethodField()
    multiply = serializers.SerializerMethodField()

    class Meta:
        model = VWTopPatients

        fields = (
            'id',
            'username',
            'name',
            'user_profile_id',
            'todo',
            'problem',
            'encounter',
            'document',
            'multiply'
        )

    def get_todo(self, obj):
        return ((float(obj.todo_count) if obj.todo_count != 0 else float(1)) * 2 / 3)

    def get_problem(self, obj):
        return (float(obj.problem_count) if obj.problem_count != 0 else float(1))

    def get_document(self, obj):
        return float(obj.encounter_count) if obj.encounter_count != 0 else float(1)

    def get_encounter(self, obj):
        return (float(obj.document_count) if obj.document_count != 0 else float(1)) / 2

    def get_multiply(self, obj):
        return ((float(obj.todo_count) if obj.todo_count != 0 else float(1)) * 2 / 3) * (
            float(obj.problem_count) if obj.problem_count != 0 else float(1)) * (
                   float(obj.encounter_count) if obj.encounter_count != 0 else float(1)) * (
                       (float(obj.document_count) if obj.document_count != 0 else float(1)) / 2)


class ProblemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Problem

        fields = (
            'id',
            'problem_name',
            'patient_id'
        )


class TodoMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = User

        fields = (
            'id',
            'first_name',
            'last_name',
            'username',
        )


class UserTodoSerializer(serializers.ModelSerializer):
    patient = SafeUserSerializer()
    problem = ProblemSerializer()
    members = TodoMemberSerializer(many=True)
    due_date = serializers.DateTimeField(format='%m/%d/%Y')

    class Meta:
        model = ToDo

        fields = (
            'id',
            'todo',
            'accomplished',
            'due_date',
            'patient',
            'labels',
            'members',
            'problem',
            'comments',
            'attachments',
            'document_set',
        )


class PatientSearchResultSerializer(serializers.ModelSerializer):
    userId = serializers.SerializerMethodField()
    fullName = serializers.SerializerMethodField()
    dob = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile

        fields = (
            'userId',
            'fullName',
            'dob'
        )

    def get_userId(self, obj):
        return obj.id

    def get_fullName(self, obj):
        return obj.user.get_full_name()

    def get_dob(self, obj):
        return obj.date_of_birth.isoformat()


class ProblemNoteSearchResultSerializer(serializers.ModelSerializer):
    author = SafeUserSerializer()
    createdAt = serializers.SerializerMethodField()
    patient = serializers.SerializerMethodField()

    class Meta:
        model = ProblemNote

        fields = (
            'author',
            'note',
            'patient',
            'createdAt',
        )

    def get_createdAt(self, obj):
        return obj.created_on.isoformat()

    def get_patient(self, obj):
        return SafeUserSerializer(obj.problem.patient).data


class GoalSearchResultSerializer(serializers.ModelSerializer):
    createdAt = serializers.SerializerMethodField()
    patient = serializers.SerializerMethodField()

    class Meta:
        model = Goal

        fields = (
            'goal',
            'patient',
            'createdAt',
        )

    def get_createdAt(self, obj):
        return obj.start_date.isoformat()

    def get_patient(self, obj):
        return SafeUserSerializer(obj.problem.patient).data


class EncounterEventSearchResultSerializer(serializers.ModelSerializer):
    patient = serializers.SerializerMethodField()
    createdAt = serializers.SerializerMethodField()

    class Meta:
        model = EncounterEvent

        fields = (
            'summary',
            'patient',
            'createdAt',
        )

    def get_createdAt(self, obj):
        return obj.datetime.isoformat()

    def get_patient(self, obj):
        return SafeUserSerializer(obj.encounter.patient).data


class TodoSearchResultSerializer(serializers.ModelSerializer):
    patient = SafeUserSerializer()
    createdAt = serializers.SerializerMethodField()

    class Meta:
        model = ToDo

        fields = (
            'todo',
            'patient',
            'createdAt',
        )

    def get_createdAt(self, obj):
        return obj.created_on.isoformat()


class MyStoryTabSearchResultSerializer(serializers.ModelSerializer):
    patient = SafeUserSerializer()
    createdAt = serializers.SerializerMethodField()

    class Meta:
        model = MyStoryTab

        fields = (
            'name',
            'patient',
            'createdAt',
        )

    def get_createdAt(self, obj):
        return obj.datetime.isoformat()


class MyStoryTextComponentSearchResultSerializer(serializers.ModelSerializer):
    patient = SafeUserSerializer()

    class Meta:
        model = MyStoryTextComponent

        fields = (
            'name',
            'patient',
            'createdAt',
        )

    def get_createdAt(self, obj):
        return obj.datetime.isoformat()


class DocumentSearchResultSerializer(serializers.ModelSerializer):
    patient = SafeUserSerializer()

    class Meta:
        model = Document

        fields = (
            'document_name',
            'patient',
        )