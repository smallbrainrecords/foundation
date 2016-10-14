

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
    