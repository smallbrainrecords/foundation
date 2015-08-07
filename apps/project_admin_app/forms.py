from django import forms


SEX_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
)

ROLE_CHOICES = (
        ('patient', 'patient'),
        ('physician', 'physician'),
        ('admin', 'admin'),
)



class UpdateBasicProfileForm(forms.Form):
	user_id = forms.IntegerField(required=True)
	first_name = forms.CharField(max_length=255, required=True)
	last_name = forms.CharField(max_length=255, required=True)


class UpdateProfileForm(forms.Form):
	user_id = forms.IntegerField(required=True)
	phone_number = forms.CharField(max_length=255, required=True)
	sex = forms.ChoiceField(choices=SEX_CHOICES, required=True)
	role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)
	summary = forms.CharField(required=False)
	cover_image = forms.ImageField(required=False)
	portrait_image = forms.ImageField(required=False)
	date_of_birth = forms.DateField(required=True)

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
	date_of_birth = forms.DateField(required=True)
	sex = forms.ChoiceField(choices=SEX_CHOICES, required=True)
	phone_number = forms.CharField(max_length=255, required=True)
	cover_image = forms.ImageField(required=False)
	portrait_image = forms.ImageField(required=False)
	summary = forms.CharField(required=False)