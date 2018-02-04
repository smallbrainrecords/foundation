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


class LoginForm(forms.Form):
    username = forms.CharField(required=True)
    password = forms.CharField(required=True)


class RegisterForm(forms.Form):
    email = forms.EmailField(required=True)
    password = forms.CharField(required=True)
    verify_password = forms.CharField(required=True)
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)


class UpdateBasicProfileForm(forms.Form):
    user_id = forms.IntegerField(required=True)
    first_name = forms.CharField(max_length=255, required=True)
    last_name = forms.CharField(max_length=255, required=True)


class UpdateProfileForm(forms.Form):
    user_id = forms.IntegerField(required=False)
    phone_number = forms.CharField(max_length=255, required=False)
    sex = forms.ChoiceField(choices=SEX_CHOICES, required=False)
    summary = forms.CharField(required=False)
    cover_image = forms.ImageField(required=False)
    portrait_image = forms.ImageField(required=False)
    date_of_birth = forms.DateField(required=False)


class UpdateEmailForm(forms.Form):
    user_id = forms.IntegerField(required=True)
    email = forms.EmailField(required=True)
