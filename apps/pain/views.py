from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response

from common.views import *
from models import PainAvatar


def create_pain_avatar(request, patient_id):
    if request.POST:
        pain_avatar = PainAvatar.objects.create(patient_id=patient_id, json=request.POST['json'])
    content = {'patient_id': patient_id}
    return render_to_response('pain/create_pain_avatar.html', content)


@login_required
@permissions_required(["update_pain"])
def add_pain_avatar(request, patient_id):

    if request.method == 'POST':
        resp = {}
        pain_avatar = PainAvatar.objects.create(patient_id=patient_id, json=request.POST['json'])
        return ajax_response(resp)

    content = {'patient_id': patient_id}
    return render_to_response('pain/add_pain_avatar.html', content)


@login_required
def view_pain_avatars(request):
    content = {'pain_avatars': PainAvatar.objects.all().order_by('-datetime')}
    return render_to_response('pain/view_pain_avatars.html', content)


@login_required
def patient_pain_avatars(request, patient_id):
    pain_avatars = PainAvatar.objects.filter(patient_id=patient_id).order_by('-datetime')
    pain_avatars_dict = [avatar.generate_dict() for avatar in pain_avatars]

    resp = {}
    resp['success'] = True
    resp['pain_avatars'] = pain_avatars_dict
    return ajax_response(resp)


@login_required
def reset(request):
    PainAvatar.objects.all().delete()
    return HttpResponse('done')
