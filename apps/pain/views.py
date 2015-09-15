
from common.views import *

from models import PainAvatar
from django.contrib.auth.models import User

from emr.manage_patient_permissions import check_permissions


def create_pain_avatar(request, patient_id):
    if request.POST:
        pain_avatar = PainAvatar(
            patient=User.objects.get(id=patient_id), json=request.POST['json'])
        pain_avatar.save()

    content = {'patient_id': patient_id}
    return render_to_response('pain/create_pain_avatar.html', content)


@login_required
def add_pain_avatar(request, patient_id):

    permissions = ['update_pain']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if request.method == 'POST' and permitted:
        resp = {}
        resp['permitted'] = permitted
        pain_avatar = PainAvatar(
            patient=User.objects.get(id=patient_id), json=request.POST['json'])
        pain_avatar.save()
        return ajax_response(resp)

    content = {'patient_id': patient_id}
    return render_to_response('pain/add_pain_avatar.html', content)


@login_required
def view_pain_avatars(request):
    content = {'pain_avatars': PainAvatar.objects.all().order_by('-datetime')}
    return render_to_response('pain/view_pain_avatars.html', content)


@login_required
def patient_pain_avatars(request, patient_id):

    patient = User.objects.get(id=patient_id)
    pain_avatars = PainAvatar.objects.filter(
        patient=patient).order_by('-datetime')

    resp = {}
    resp['success'] = True

    pain_avatars_holder = []
    for avatar in pain_avatars:
        pain_avatars_holder.append(avatar.generate_dict())

    resp['pain_avatars'] = pain_avatars_holder

    return ajax_response(resp)


@login_required
def reset(request):
    [i.delete() for i in PainAvatar.objects.all()]
    return HttpResponse('done')
