from django.shortcuts import render 
from django.shortcuts import render_to_response
from django.db.models.loading import get_model
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from django.template import RequestContext
from models import UserProfile, AccessLog, Problem, Goal, ToDo, Guideline, TextNote, PatientImage, Encounter, EncounterEvent, EventSummary, Sharing, Viewer, ViewStatus, ProblemRelationship
import traceback
from django.contrib.auth.decorators import login_required
import json
import os

class AccessLogMiddleware(object):

    def process_request(self, request):
        if request.user.is_authenticated() and not request.path.startswith('/list_of'):
            access_log = AccessLog(user=request.user, summary=request.path)
            access_log.save()

from django.http import *
from django.shortcuts import render_to_response,redirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
 
def login_user(request):
    logout(request)
    username = password = ''
    
          

    if request.POST:
        email = request.POST['email']
        password = request.POST['password']
        u,created = User.objects.get_or_create(username=email)
        if created:
            u.set_password(password)
            u.email = email
            u.save()
        user = authenticate(username=email, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect('/')
    return render_to_response('login.html', context_instance=RequestContext(request))

def register(request):
    if request.POST:
        email = request.POST['email']
        password = request.POST['password']
        if request.POST['password'] != request.POST['password_confirm']:
            return HttpResponseRedirect('/')
        u,created = User.objects.get_or_create(username=email, email=email)
        if created:
            u.set_password(password)
            u.first_name = request.POST['first_name']
            u.last_name = request.POST['last_name']
            u.save()
            user = authenticate(username=email, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return HttpResponseRedirect('/')
        return HttpResponseRedirect('/')

from django.contrib.auth.decorators import user_passes_test

@user_passes_test(lambda u: u.is_superuser)
def update(request):
    os.system('sh /home/tim/core/update.sh &')
    html = """
    <script src="//code.jquery.com/jquery-1.11.0.min.js"></script>
    <title>Update</title>
    <script>
    var seconds = 60;
    setInterval(function() { $('#time_left').text(seconds); seconds -= 1; }, 1000);
    setTimeout(function() { window.location = "/" }, 60000);
    </script> Going to homepage in <span id="time_left">60</span> seconds
    """
    return HttpResponse(html)

@login_required
def home(request):
    try:
        
        profile = UserProfile.objects.get(user=request.user)
        role = profile.role
        context = {}
        context['role'] = role
        context = RequestContext(request, context)
        if (role == 'patient'):
            return view_patient(request, request.user.id)
        
        return render_to_response("home.html", context)

    except: 
        traceback.print_exc()
        if request.user.is_superuser:
            context = {}
            context['role'] = 'admin'
            context = RequestContext(request, context)
            return render_to_response("home.html", context)

            
        return HttpResponse('<script>setTimeout(function() { window.location = "/" }, 1000);</script> Waiting on manual approval')
    
@login_required
def list_of_unregistered_users(request):
    
    users = []
    for user in User.objects.all():
        try:
            profile = UserProfile.objects.get(user=user)
        except:
            users.append({'id': user.id, 'username': user.username, 'full_name': user.get_full_name()})
    return HttpResponse(json.dumps(users), content_type="application/json")

@login_required
def register_users(request): 
    for i in request.POST:
        try:
            user_profile = UserProfile(user=User.objects.get(id=i.split('_')[1]), role=request.POST[i])
            user_profile.save()
            if (request.POST[i] == 'admin'):
                user = User.objects.get(id=i.split('_')[1])
                user.is_superuser = True
                user.is_staff = True
                user.save()
        except:
            pass
    return HttpResponse('saved')


def is_patient(user):
    try:
        profile = UserProfile.objects.get(user=user)
        return profile.role == 'patient'
    except:
        return False
    

@login_required
def list_users(request):

    users = [{'is_patient': is_patient(user), 'username': user.username, 'firstname': user.first_name, 'lastname': user.last_name, 'id': user.id, 'sex': UserProfile.objects.get(user=user).sex, 'contact_number': UserProfile.objects.get(user=user).phone_number, 'birthday': UserProfile.objects.get(user=user).date_of_birth.strftime('%m/%d/%Y') if UserProfile.objects.get(user=user).date_of_birth else ''} for user in User.objects.all().order_by('first_name') if UserProfile.objects.filter(user=user)]
    return HttpResponse(json.dumps(users), content_type="application/json")

@login_required
def view_patient(request, user_id):
    role = UserProfile.objects.get(user=request.user).role
    
    from pain.models import PainAvatar
    user = User.objects.get(id=user_id)
    # allowed viewers are the patient, admin/physician, and other patients the patient has shared to
    if (not ((request.user == user) or (role in ['admin', 'physician']) or (Sharing.objects.filter(patient=user, other_patient=request.user, all=True)))):
        return HttpResponse("Not allowed")
    if (not is_patient(user)):
        return HttpResponse("Error: this user isn't a patient")
    context = {'patient': user, 'user_role': UserProfile.objects.get(user=request.user).role, 'patient_profile': UserProfile.objects.get(user=user), 'problems': Problem.objects.filter(patient=user)}
    context.update({'pain_avatars': PainAvatar.objects.filter(patient=user).order_by('-datetime')})
    context['encounters'] = Encounter.objects.filter(patient=user).order_by('-starttime')
    import settings
    context['voice_control'] = settings.VOICE_CONTROL
    context['syncing'] = settings.SYNCING
    if (request.user == user):
        context['shared_patients'] = list(set([i.patient for i in Sharing.objects.filter(other_patient=user)]))
    context = RequestContext(request, context)
    try:
        encounter = Encounter.objects.filter(patient=user, stoptime__isnull=True).order_by('-starttime')[0]
        context['current_encounter'] = encounter
    except:
        pass
    import os
    improt re
    context['problem_elements'] = [ re.search('problem_(?P<element>\w+)', f).group('element') for f in listdir('/root/foundation/static/js/problems/') if not f == 'problem_element_template.js']
    return render_to_response("patient.html", context)

@login_required
def get_patient_data(request, patient_id):
    
    # Find out if user requesting the data is admin, physician, or patient
    role_of_user_requesting_the_data = UserProfile.objects.get(user=request.user).role
    # Get patient object from patient id
    patient = User.objects.get(id=patient_id)
    # We provide the problems, goals, notes, todos
    # and concept ids of the problems as well as the snomed parents and children of those problems mapped to a problem id
    # This way we can prevent duplicate problems from being added
    viewers = []
    from datetime import datetime, timedelta

    time_threshold = datetime.now() - timedelta(seconds=5)
    viewers = list(set([viewer.viewer for viewer in Viewer.objects.filter(patient=patient, datetime__gte=time_threshold)]))
    raw_viewers = []
    print 'viewers: '+str(viewers)
    for viewer in viewers:
        print 'viewer: '+str(viewer)
        raw_viewers.append({'user_id': viewer.id, 'full_name': viewer.get_full_name()})
    viewers = raw_viewers
    view_status = {}
    vs = ViewStatus.objects.filter(patient=patient)
    if vs:
        if not viewers:
            vs[0].delete()
        else:
            try:
                
                view_status = json.loads(vs[0].status)
            except:
                pass
            
    # this tracking section lets us coordinate multiple people/browser windows/tabs accessing a patient page at the same time
    if 'tracking_id' in request.GET:
        tracking_id = request.GET['tracking_id']
        patient = User.objects.get(id=patient_id)
        
        p, created = Viewer.objects.get_or_create(patient=patient, viewer=request.user, tracking_id=tracking_id)
        p.save()
    if 'new_status' in request.GET:
        patient = User.objects.get(id=patient_id)
        p, created = ViewStatus.objects.get_or_create(patient=patient)
        p.status = request.GET['new_status']
        p.save()
    
    # allowed viewers are the patient, admin/physician, and other patients the patient has shared to
    if (not ((request.user == patient) or (role_of_user_requesting_the_data in ['admin', 'physician']) or (Sharing.objects.filter(patient=patient, other_patient=request.user)))):
        return HttpResponse("Not allowed")
    # Right now only users with role == patient have a patient page
    if (not is_patient(patient)):
        return HttpResponse("Error: this user isn't a patient")
    
    data = {'problems': {'is_active': [], 'not_active': []}, 'goals': {'not_accomplished': [], 'accomplished': []}, 'notes': [], 'todos': {'not_accomplished': [], 'accomplished': []}, 'concept_ids': {}, 'viewers': viewers, 'view_status': view_status}
    if 'get_only_status' in request.GET:
        return HttpResponse(json.dumps(data), content_type="application/json")
    # At this point we know the user is allowed to view this patient. 
    # Now we have to detrimine what data can be provided to the requesting user
    # If the user requesting the patient data is the targeted patient or an admin or physician then we know it's OK to provide all the data
   # if ((request.user == patient) or (role_of_user_requesting_the_data in ['admin', 'physician'])):
        # Get all problems for the patient 
        #problems_query = Problem.objects.filter(patient=patient).order_by('problem_name').order_by('-authenticated')
    # Otherwise the requesting user is only allowed to see some of the patient's info    
    #else:
        # Get just the problems shared to the user
    #    problems_query = [i.item for i in Sharing.objects.filter(content_type=ContentType.objects.get(app_label="emr", model="problem"), patient=patient, other_patient=request.user)]
    problems_query = Problem.objects.filter(patient=patient).order_by('problem_name').order_by('-authenticated')
    
    for problem in problems_query.filter(is_active=True):
        # We store the data for this problem in a dictionary called "d"
        d = {}
        d['problem_id'] = problem.id
        d['start_date'] = problem.start_date.strftime('%m/%d/%Y')
        effected_by = {}
        for i in problems_query.filter(is_active=True):
            if i == problem:
                continue
            elif ProblemRelationship.objects.filter(source=i, target=problem):
                effected_by[int(i.id)] = True
            else:
                effected_by[int(i.id)] = False
        d['effected_by'] = effected_by
        affects = {}
        for i in problems_query.filter(is_active=True):
            if i == problem:
                continue
            elif ProblemRelationship.objects.filter(source=problem, target=i):
                affects[int(i.id)] = True
            else:
                affects[int(i.id)] = False
        d['affects'] = affects
        d['problem_name'] = problem.problem_name
        d['images'] = [g.image.url for g in PatientImage.objects.filter(problem=problem)]
        d['guidelines'] = [{'guideline': g.guideline, 'reference_url': g.reference_url} for g in Guideline.objects.filter(concept_id=problem.concept_id)]
        d['is_controlled'] = problem.is_controlled
        d['is_authenticated'] = problem.authenticated
        d['is_active'] = problem.is_active
        d['goals'] = [{'id': g.id, 'start_date': g.start_date.strftime('%m/%d/%Y'), 'goal': g.goal, 'is_controlled': g.is_controlled, 'accomplished': g.accomplished, 'notes': [{'note': n.note} for n in g.notes.all().order_by('-datetime')]} for g in Goal.objects.filter(problem=problem, accomplished=False)]
        d['todos'] = [{'todo': g.todo, 'id': g.id, 'accomplished': g.accomplished} for g in ToDo.objects.filter(problem=problem, accomplished=False)]
        d['notes'] = {'by_physician': [{'note': g.note} for g in TextNote.objects.filter(problem=problem, by__in=['physician', 'admin']).order_by('-datetime')], 'by_patient': [{'note': g.note} for g in TextNote.objects.filter(problem=problem, by='patient').order_by('-datetime')], 'all': [{'by': g.by, 'note': g.note} for g in TextNote.objects.filter(problem=problem)]}
        data['problems']['is_active'].append(d)
        try:
            data['concept_ids'][problem.concept_id] = problem.id
            import pymedtermino.snomedct
            for j in [i.__dict__ for i in pymedtermino.snomedct.SNOMEDCT[int(problem.concept_id)].parents]:
                data['concept_ids'][j['code']] = problem.id
            for j in [i.__dict__ for i in pymedtermino.snomedct.SNOMEDCT[int(problem.concept_id)].children]:
                data['concept_ids'][j['code']] = problem.id
        except:
            pass
    for problem in problems_query.filter(is_active=False):
        # We store the data for this problem in a dictionary called "d"
        d = {}
        d['problem_id'] = problem.id
        d['start_date'] = problem.start_date.strftime('%m/%d/%Y')
        d['effected_by'] = problem.parent.id if problem.parent else None
        d['affects'] = [{'problem_id': g.id, 'problem_name': g.problem_name} for g in problem.get_children()]
        d['problem_name'] = problem.problem_name
        d['images'] = [g.image.url for g in PatientImage.objects.filter(problem=problem)]
        d['guidelines'] = [{'guideline': g.guideline, 'reference_url': g.reference_url} for g in Guideline.objects.filter(concept_id=problem.concept_id)]
        d['is_controlled'] = problem.is_controlled
        d['is_authenticated'] = problem.authenticated
        d['is_active'] = problem.is_active
        d['goals'] = [{'id': g.id, 'start_date': g.start_date.strftime('%m/%d/%Y'), 'goal': g.goal, 'is_controlled': g.is_controlled, 'accomplished': g.accomplished, 'notes': [{'note': n.note} for n in g.notes.all().order_by('-datetime')]} for g in Goal.objects.filter(problem=problem, accomplished=False)]
        d['todos'] = [{'todo': g.todo, 'id': g.id, 'accomplished': g.accomplished} for g in ToDo.objects.filter(problem=problem, accomplished=False)]
        d['notes'] = {'by_physician': [{'note': g.note} for g in TextNote.objects.filter(problem=problem, by__in=['physician', 'admin']).order_by('-datetime')], 'by_patient': [{'note': g.note} for g in TextNote.objects.filter(problem=problem, by='patient').order_by('-datetime')], 'all': [{'by': g.by, 'note': g.note} for g in TextNote.objects.filter(problem=problem)]}
        data['problems']['not_active'].append(d)
        try:
            data['concept_ids'][problem.concept_id] = problem.id
            import pymedtermino.snomedct
            for j in [i.__dict__ for i in pymedtermino.snomedct.SNOMEDCT[int(problem.concept_id)].parents]:
                data['concept_ids'][j['code']] = problem.id
            for j in [i.__dict__ for i in pymedtermino.snomedct.SNOMEDCT[int(problem.concept_id)].children]:
                data['concept_ids'][j['code']] = problem.id
        except:
            pass
    for goal in Goal.objects.filter(patient=patient, accomplished=False).order_by('goal'):
        d = {}
        d['for_problem'] = goal.problem.problem_name if goal.problem else ''
        d['goal_id'] = goal.id
        d['goal'] = goal.goal
        d['start_date'] = goal.start_date.strftime('%m/%d/%y')
        d['is_controlled'] = goal.is_controlled
        d['accomplished'] = goal.accomplished
        d['notes'] = [{'note': n.note} for n in goal.notes.all().order_by('-datetime')]
        data['goals']['not_accomplished'].append(d)
    for todo in ToDo.objects.filter(patient=patient, accomplished=False).order_by('todo'):
        d = {}
        d['for_problem'] = todo.problem.problem_name if todo.problem else ''
        d['todo_id'] = todo.id
        d['todo'] = todo.todo
        d['accomplished'] = todo.accomplished
        data['todos']['not_accomplished'].append(d)
    for todo in ToDo.objects.filter(patient=patient, accomplished=True).order_by('todo'):
        d = {}
        d['for_problem'] = todo.problem.problem_name if todo.problem else ''
        d['todo_id'] = todo.id
        d['todo'] = todo.todo
        d['accomplished'] = todo.accomplished
        data['todos']['accomplished'].append(d)
        
        
    return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def change_status(request):
    role = UserProfile.objects.get(user=request.user).role

    authenticated = True if (role == 'physician' or role == 'admin') else False
    print request.POST
    if request.POST['target'] == 'problem':
        problem = Problem.objects.get(id=request.POST['id'])
        problem.authenticated = authenticated
        value = True if request.POST['value'] == 'true' else False
        if (request.POST['attr'] == 'authenticated' and role == 'patient'):
            return HttpResponse("patients can't authenticate problems")

        setattr(problem,request.POST['attr'], value)
        problem.save()
    elif request.POST['target'] == 'goal':
        goal = Goal.objects.get(id=request.POST['id'])
        if goal.problem:
            goal.problem.authenticated = authenticated
            goal.problem.save()
        value = True if request.POST['value'] == 'true' else False
        setattr(goal,'accomplished', value)
        goal.save()
    elif request.POST['target'] == 'goal_is_controlled':
        
        goal = Goal.objects.get(id=request.POST['id'])
        if goal.problem:
            goal.problem.authenticated = authenticated
            goal.problem.save()
        value = True if request.POST['value'] == 'true' else False
        setattr(goal,'is_controlled', value)
        goal.save()
    elif request.POST['target'] == 'todo':
        todo = ToDo.objects.get(id=request.POST['id'])
        if todo.problem:
            todo.problem.authenticated = authenticated
            todo.problem.save()
        value = True if request.POST['value'] == 'true' else False
        setattr(todo,'accomplished', value)
        todo.save()
    elif request.POST['attr'] == 'effected_by':
        problem = Problem.objects.get(id=request.POST['id'])
        problem.authenticated = authenticated
        problem.save()
        if request.POST['value'] == 'true':
            pr = ProblemRelationship(source=Problem.objects.get(id=request.POST['target']), target=Problem.objects.get(id=request.POST['id']))
            pr.save()
        else:
            pr = ProblemRelationship.objects.get(source=Problem.objects.get(id=request.POST['target']), target=Problem.objects.get(id=request.POST['id']))
            pr.delete()
    elif request.POST['attr'] == 'affects':
        problem = Problem.objects.get(id=request.POST['id'])
        problem.authenticated = authenticated
        problem.save()
        if request.POST['value'] == 'true':
            pr = ProblemRelationship(source=Problem.objects.get(id=request.POST['id']), target=Problem.objects.get(id=request.POST['target']))
            pr.save()
        else:
            pr = ProblemRelationship.objects.get(source=Problem.objects.get(id=request.POST['id']), target=Problem.objects.get(id=request.POST['target']))
            pr.delete()
    return HttpResponse('saved')

@login_required
def submit_data_for_problem(request, problem_id):
    print request.POST
    role = UserProfile.objects.get(user=request.user).role

    authenticated = True if (role == 'physician' or role == 'admin') else False

    if request.POST['type'] == 'note':
        
        problem = Problem.objects.get(id=problem_id)
        problem.authenticated = authenticated
        note = TextNote(by=UserProfile.objects.get(user=request.user).role, note=request.POST['data'])
        note.save()
        problem.notes.add(note)
        problem.save()
    elif request.POST['type'] == 'problem_parent':
        
        problem = Problem.objects.get(id=problem_id)
        problem.authenticated = authenticated
        if (request.POST['data'] == 'none'):
            problem.parent = None
        else:
            problem.parent = Problem.objects.get(id=request.POST['data'])
        problem.save()
    elif request.POST['type'] == 'problem_start_date':
        print 'problem_start_date: '+str(request.POST)
        problem = Problem.objects.get(id=problem_id)
        problem.authenticated = authenticated
        from datetime import datetime
        if not request.POST['data'].index('/') == 2:
            problem.start_date = datetime.strptime('0' + request.POST['data'], "%m/%d/%Y")
        else:
            problem.start_date = datetime.strptime(request.POST['data'], "%m/%d/%Y")
        problem.save()
    elif request.POST['type'] == 'note_for_goal':

        goal = Goal.objects.get(id=problem_id)
        note = TextNote(by=UserProfile.objects.get(user=request.user).role, note=request.POST['data'])
        note.save()
        goal.notes.add(note)
        goal.save()
        if goal.problem:
            problem = goal.problem
            problem.authenticated = authenticated
            problem.save()
    elif request.POST['type'] == 'mark_parent':
        problem = Problem.objects.get(id=problem_id)
        problem.authenticated = authenticated
        if (request.POST['data'] == 'none'):
            problem.parent = None
        else:
            problem.parent = Problem.objects.get(id=request.POST['data'])
        problem.save()
    else:
        problem = Problem.objects.get(id=problem_id)
        problem.authenticated = authenticated
        problem.save()
        model = get_model('emr', request.POST['type'].capitalize()) 
    
        m = model(patient=problem.patient, problem=problem)
        setattr(m,request.POST['type'], request.POST['data'] ) 
        m.save()
        return HttpResponse(m.id)
    return HttpResponse('saved')

@login_required
def add_problem(request, patient_id):
    role = UserProfile.objects.get(user=request.user).role
    authenticated = True if (role == 'physician' or role == 'admin') else False
    if 'problem_name' in request.POST:
        problem = Problem(patient=User.objects.get(id=patient_id), problem_name=request.POST['problem_name'], concept_id=request.POST['concept_id'], authenticated=authenticated)
        problem.save()
    elif 'goal' in request.POST:
        goal = Goal(patient=User.objects.get(id=patient_id), goal=request.POST['goal'])
        goal.save()
    elif 'todo' in request.POST:
        print 'todo'
        print request.POST
        todo = ToDo(patient=User.objects.get(id=patient_id), todo=request.POST['todo'])
        todo.save()
    return HttpResponse('added')

@login_required
def list_snomed_terms(request):
    # We list snomed given a query
    query = request.GET['query']
    
    import pymedtermino.snomedct
    raw_results = pymedtermino.snomedct.SNOMEDCT.search(query)
    matching_disorders = [i.__dict__ for i in raw_results if '(disorder)' in i.__dict__['term']]
    matching_disorders = sorted(matching_disorders, key=lambda x: x["term"])
    matching_findings = [i.__dict__ for i in raw_results if '(finding)' in i.__dict__['term']]
    matching_findings = sorted(matching_findings, key=lambda x: x["term"])
    results = []
    results.extend(matching_disorders)
    results.extend(matching_findings)
    results = json.dumps(results)
    return HttpResponse(results, content_type="application/json")

@login_required
def upload_image_to_problem(request, problem_id):
    if request.POST:
        role = UserProfile.objects.get(user=request.user).role

        authenticated = True if (role == 'physician' or role == 'admin') else False
        problem = Problem.objects.get(id=problem_id)
        problem.authenticated = authenticated
        problem.save()
        patient_image = PatientImage(patient=Problem.objects.get(id=problem_id).patient, problem=Problem.objects.get(id=problem_id), image=request.FILES['file'])
        patient_image.save()
        try:
            encounter = Encounter.objects.filter(patient=problem.patient, stoptime__isnull=True).order_by('-starttime')[0]
            event_summary = EventSummary(patient=problem.patient, summary='Physician added image<br/><a href="/media/%s"><img src="/media/%s" style="max-width:100px; max-height:100px" /></a>' % (patient_image.image, patient_image.image))
            event_summary.save()
            
            ctype = ContentType.objects.get_for_model(event_summary)
            encounter_event = EncounterEvent(content_type=ctype, object_id=event_summary.id)
            encounter_event.save()
            encounter.events.add(encounter_event)
            encounter.save()
        except:
            pass
        return HttpResponseRedirect('/patient/%s/' % (Problem.objects.get(id=problem_id).patient.id))
    else:
        context = RequestContext(request, {})
        return render_to_response('upload_image_to_problem.html', context)

@login_required
def create_encounter(request, patient_id):
    encounter = Encounter(patient=User.objects.get(id=patient_id), physician=User.objects.get(id=request.user.id))
    encounter.save()
    return HttpResponse(encounter.id, content_type="text/plain")

@login_required
def stop_encounter(request, encounter_id):
    from datetime import datetime
    encounter = Encounter.objects.get(id=encounter_id)
    encounter.stoptime = datetime.now()
    encounter.save()
    return HttpResponse('saved', content_type="text/plain")

from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
@login_required 
def save_event_summary(request):
    event_summary = EventSummary(patient=User.objects.get(id=request.POST['patient_id']), summary=request.POST['summary'])
    event_summary.save()
    encounter = Encounter.objects.get(id=request.POST['encounter_id'])
    ctype = ContentType.objects.get_for_model(event_summary)
    encounter_event = EncounterEvent(content_type=ctype, object_id=event_summary.id)
    encounter_event.save()
    encounter.events.add(encounter_event)
    encounter.save()
    return HttpResponse('')

@login_required
def encounter(request, encounter_id):
   
    print 'encounter debug'
    print request.POST
    print request.FILES
    if 'note' in request.POST:
        encounter = Encounter.objects.get(id=encounter_id)
        encounter.note = request.POST['note']
        encounter.save()
    if 'audio_file' in request.FILES:
        encounter = Encounter.objects.get(id=encounter_id)
        encounter.audio = request.FILES['audio_file']
        encounter.save()
    if 'video_file' in request.FILES:
        encounter = Encounter.objects.get(id=encounter_id)
        encounter.video = request.FILES['video_file']
        encounter.save()
    role_of_user_requesting_the_data = UserProfile.objects.get(user=request.user).role    
    encounter = Encounter.objects.get(id=encounter_id)    
    patient = encounter.patient        
    if (not ((request.user == patient) or (role_of_user_requesting_the_data in ['admin', 'physician']) or (Sharing.objects.filter(patient=patient, other_patient=request.user)))):
        return HttpResponse("Not allowed")         
    context = {'encounter': Encounter.objects.get(id=encounter_id), 'events': Encounter.objects.get(id=encounter_id).events.all().order_by('datetime'), 'patient': Encounter.objects.get(id=encounter_id).patient}
    context = RequestContext(request, context)
    return render_to_response("encounter.html", context)

def save_patient_summary(request, patient_id):
    profile = UserProfile.objects.get(user=User.objects.get(id=patient_id))
    profile.summary = request.POST['summary']
    profile.save()
    return HttpResponseRedirect('/patient/%s/' % (patient_id))

from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic.base import View
from social_auth.exceptions import AuthFailed
from social_auth.views import complete
 
 
  
class AuthComplete(View):
    def get(self, request, *args, **kwargs):
        backend = kwargs.pop('backend')
        try:
            return complete(request, backend, *args, **kwargs)
        except AuthFailed:
            messages.error(request, "Your Google Apps domain isn't authorized for this app")
            return HttpResponseRedirect(reverse('home'))
 
 
class LoginError(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse(status=401)   
