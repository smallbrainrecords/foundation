
from common.views import * 

from models import PainAvatar
from django.contrib.auth.models import User


def create_pain_avatar(request, patient_id):
    if request.POST:
        pain_avatar = PainAvatar(patient=User.objects.get(id=patient_id), json=request.POST['json'])
        pain_avatar.save()
    return render_to_response('pain/create_pain_avatar.html', {'patient_id': patient_id})

@login_required
def add_pain_avatar(request, patient_id):
    if request.POST:
        pain_avatar = PainAvatar(patient=User.objects.get(id=patient_id), json=request.POST['json'])
        pain_avatar.save()
        return HttpResponse('ok')
    return render_to_response('pain/add_pain_avatar.html', {'patient_id': patient_id})


def view_pain_avatars(request):
    return render_to_response('pain/view_pain_avatars.html', {'pain_avatars': PainAvatar.objects.all().order_by('-datetime')})


def patient_pain_avatars(request, patient_id):

	patient = User.objects.get(id=patient_id)
	pain_avatars = PainAvatar.objects.filter(patient=patient).order_by('-datetime')

	resp = {}
	resp['success'] = True

	pain_avatars_holder = []
	for avatar in pain_avatars:
		pain_avatars_holder.append(avatar.generate_dict())

	resp['pain_avatars'] = pain_avatars_holder

	return HttpResponse(json.dumps(resp))

	
def reset(request):
    [i.delete() for i in PainAvatar.objects.all()]
    return HttpResponse('done')
