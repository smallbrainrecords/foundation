

from common.views import *

from emr.models import UserProfile

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
	user_profiles_holder = [ x.generate_dict() for x in user_profiles ]

	return ajax_response(user_profiles_holder)
	



