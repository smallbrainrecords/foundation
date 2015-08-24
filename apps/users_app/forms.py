

from django import forms



class LoginForm(forms.Form):
	username = forms.CharField(required=True)
	password = forms.CharField(required=True)


class RegisterForm(forms.Form):

	email = forms.EmailField(required=True)
	password = forms.CharField(required=True)
	verify_password = forms.CharField(required=True)
	first_name = forms.CharField(required=False)
	last_name = forms.CharField(required=False)
