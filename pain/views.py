from django.shortcuts import render
from django.shortcuts import render_to_response
from django.db.models.loading import get_model
from django.http import HttpResponse, HttpResponseRedirect
from models import PainAvatar
from django.contrib.auth.models import User

def create_pain_avatar(request, patient_id):
    if request.POST:
        pain_avatar = PainAvatar(patient=User.objects.get(id=patient_id), json=request.POST['json'])
        pain_avatar.save()
    return render_to_response('pain/create_pain_avatar.html', {'patient_id': patient_id})

def view_pain_avatars(request):
    return render_to_response('pain/view_pain_avatars.html', {'pain_avatars': PainAvatar.objects.all().order_by('-datetime')})

def reset(request):
    [i.delete() for i in PainAvatar.objects.all()]
    return HttpResponse('done')
