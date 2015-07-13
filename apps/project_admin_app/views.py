

from common.views import *

from django.contrib.auth.models import User
from emr.models import UserProfile

from users_app.serializers import UserProfileSerializer

@login_required
def home(request):

	content = {}

	return render(
		request,
		'project_admin/home.html',
		content)


@login_required
def list_users(request):

	user_profiles = UserProfile.objects.all()
	user_profiles_holder = UserProfileSerializer(user_profiles, many=True).data

	return ajax_response(user_profiles_holder)
	


@login_required
def user_info(request, user_id):

	resp={}
	resp['success'] = False

	user = User.objects.get(id=user_id)
	user_profile = UserProfile.objects.get(user=user)

	user_profile_dict = UserProfileSerializer(user_profile).data

	resp['success'] = True
	resp['user_profile'] = user_profile_dict
	return ajax_response(resp)


