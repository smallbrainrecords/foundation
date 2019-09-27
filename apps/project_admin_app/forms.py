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
from django import forms

SEX_CHOICES = (
    ('male', 'Male'),
    ('female', 'Female'),)

ROLE_CHOICES = (
    ('patient', 'Patient'),
    ('physician', 'Physician'),
    ('mid-level', 'Mid Level PA/NP'),
    ('nurse', 'Nurse'),
    ('secretary', 'Secretary'),
    ('admin', 'Admin'),)

MEMBER_TYPE_CHOICES = (
    ('patient', 'Patient'),
    ('mid-level', 'Mid Level PA/NP'),
    ('nurse', 'Nurse'),
    ('secretary', 'Secretary'),)


class UpdateBasicProfileForm(forms.Form):
    user_id = forms.IntegerField(required=True)
    first_name = forms.CharField(max_length=255, required=True)
    last_name = forms.CharField(max_length=255, required=True)


class UpdateProfileForm(forms.Form):
    user_id = forms.IntegerField(required=True)
    phone_number = forms.CharField(max_length=255, required=False)
    sex = forms.ChoiceField(choices=SEX_CHOICES, required=False)
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=False)
    summary = forms.CharField(required=False)
    cover_image = forms.ImageField(required=False)
    portrait_image = forms.ImageField(required=False)
    date_of_birth = forms.DateField(required=False)


class UpdatePasswordForm(forms.Form):
    user_id = forms.IntegerField(required=True)
    new_password = forms.CharField(max_length=255, required=True)
    verify_password = forms.CharField(max_length=255, required=True)


class UpdateEmailForm(forms.Form):
    user_id = forms.IntegerField(required=True)
    email = forms.EmailField(required=True)


class CreateUserForm(forms.Form):
    first_name = forms.CharField(max_length=255, required=True)
    last_name = forms.CharField(max_length=255, required=True)
    username = forms.CharField(max_length=255, required=True)
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)
    password = forms.CharField(max_length=255, required=True)
    verify_password = forms.CharField(max_length=255, required=True)
    date_of_birth = forms.DateField(required=False)
    sex = forms.ChoiceField(choices=SEX_CHOICES, required=False)
    phone_number = forms.CharField(max_length=255, required=False)
    cover_image = forms.ImageField(required=False)
    portrait_image = forms.ImageField(required=False)
    summary = forms.CharField(required=False)


class AssignPhysicianMemberForm(forms.Form):
    user_id = forms.CharField(max_length=255, required=True)
    member_type = forms.ChoiceField(choices=MEMBER_TYPE_CHOICES, required=True)
    physician_id = forms.CharField(max_length=255, required=True)


class UpdateActiveForm(forms.Form):
    user_id = forms.IntegerField(required=True)
    is_active = forms.BooleanField(required=False)
    active_reason = forms.CharField(required=False)


class UpdateDeceasedDateForm(forms.Form):
    user_id = forms.IntegerField(required=True)
    deceased_date = forms.CharField(required=False)
