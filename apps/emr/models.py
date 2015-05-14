from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from mptt.models import MPTTModel, TreeForeignKey

def instance_dict(instance, key_format=None):
    """
    Returns a dictionary containing field names and values for the given
    instance
    """
    from django.db.models.fields import DateField
    from django.db.models.fields.related import ForeignKey
    if key_format:
        assert '%s' in key_format, 'key_format must contain a %s'
    key = lambda key: key_format and key_format % key or key

    pk = instance._get_pk_val()
    d = {}

    for field in instance._meta.fields:
        attr = field.name
        if hasattr(instance, attr):  # django filer broke without this check
            value = getattr(instance, attr)
            if value is not None:
                if isinstance(field, ForeignKey):
                    fkey_values = instance_dict(value)
                    for k, v in fkey_values.items():
                        d['%s.%s' % (key(attr), k)] = v
                        continue
                elif isinstance(field, DateField):
                    value = value.strftime('%Y-%m-%d')
        d[key(attr)] = value
    for field in instance._meta.many_to_many:
        if pk:
            d[key(field.name)] = [
            obj._get_pk_val()
            for obj in getattr(instance, field.attname).all()]
        else:
            d[key(field.name)] = []
    return d



ROLE_CHOICES = (
        ('patient', 'patient'),
        ('physician', 'physician'),
        ('admin', 'admin'),
)


SEX_CHOICES = (
        ('male', 'male'),
        ('female', 'female'),
)

class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='patient')
    data = models.TextField(blank=True) 
    cover_image = models.ImageField(upload_to='cover_image/', blank=True)
    portrait_image = models.ImageField(upload_to='cover_image/', blank=True)
    summary = models.TextField(blank=True)

    sex = models.CharField(max_length=6, choices=SEX_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    
    def __unicode__(self):
        return '%s' % (self.user.get_full_name())
        
    def get_dict(self):
        return instance_dict(self)


    def generate_dict(self):
        obj_dict = {}
        obj_dict['first_name'] = self.user.first_name
        obj_dict['last_name'] = self.user.last_name
        obj_dict['role'] = self.role
        obj_dict['data'] = self.data
        obj_dict['summary'] = self.summary
        obj_dict['sex'] = self.sex
        obj_dict['date_of_birth'] = str(self.date_of_birth)
        obj_dict['phone_number'] = self.phone_number
        obj_dict['cover_image'] = self.cover_image.url
        obj_dict['portrait_image'] = self.portrait_image.url

        return obj_dict


class AccessLog(models.Model):
    user = models.ForeignKey(User)
    datetime = models.DateTimeField(auto_now_add=True)
    summary = models.TextField()

    def __unicode__(self):
        return '%s %s %s' % (self.user.username, self.datetime, self.summary)

        
    def get_dict(self):
        return instance_dict(self)

def get_path(instance, filename):
    try:
        return '%s/%s/%s' % (instance.patient.id, instance.problem.id, filename)
    except:
        return '%s/%s' % (instance.patient.id, filename)

        
    def get_dict(self):
        return instance_dict(self)
 
class Encounter(models.Model):
    physician = models.ForeignKey(User, related_name="physician")
    patient = models.ForeignKey(User, related_name="patient")
    starttime = models.DateTimeField(auto_now_add=True)
    stoptime = models.DateTimeField(null=True, blank=True)
    #events = generic.GenericRelation('EncounterEvent',
    #    content_type_field='content_type',
    #    object_id_field='object_id'
    #)
    events = models.ManyToManyField('EncounterEvent', blank=True)
    audio = models.FileField(upload_to=get_path, blank=True) 
    video = models.FileField(upload_to=get_path, blank=True)
    note = models.TextField(blank=True)
    
    def __unicode__(self):
        return 'Patient: %s Time: %s' % (self.patient.get_full_name(), self.physician.get_full_name())

        
    def get_dict(self):
        return instance_dict(self)

    def generate_dict(self):
        obj_dict = {}

        obj_dict['id'] = self.id
        obj_dict['physician'] = unicode(self.physician)
        obj_dict['patient'] = unicode(self.patient)
        obj_dict['starttime'] = str(self.starttime.strftime("%Y-%m-%d %H:%M"))
        obj_dict['stoptime'] = str(self.stoptime.strftime("%Y-%m-%d %H:%M"))
        obj_dict['duration'] = str(self.stoptime-self.starttime)

        obj_dict['note'] = self.note

        return obj_dict



class EncounterEvent(models.Model):
    datetime = models.DateTimeField(auto_now_add=True)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    event = generic.GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return unicode(self.event)
        
        
    def get_dict(self):
        return instance_dict(self)

    def video_seconds(self):
        import datetime
        import time
        # find the Encounter (Wish I had made a foreignkey would be much easier to find)
        for encounter in Encounter.objects.all():
            if self in encounter.events.all():
                encounter = encounter
                break
        x = encounter.starttime
        s = int(datetime.timedelta(hours=x.hour,minutes=x.minute,seconds=x.second).total_seconds())
        x = self.datetime
        e = int(datetime.timedelta(hours=x.hour,minutes=x.minute,seconds=x.second).total_seconds())
        return e - s
        
    def video_timestamp(self):
        seconds = self.video_seconds()
        h = seconds // 60
        s = seconds % 60
        if s < 10:
            s = '0' + str(s)
        return '%s:%s' % (h, s)
        
class EventSummary(models.Model):
    patient = models.ForeignKey(User)
    datetime = models.DateTimeField(auto_now_add=True)
    summary = models.TextField()

    def __unicode__(self):
        return '%s %s' % (unicode(self.patient), self.summary)

        
    def get_dict(self):
        return instance_dict(self)

    def video_seconds(self):
        import datetime
        import time
        x = self.datetime
        return int(datetime.timedelta(hours=x.tm_hour,minutes=x.tm_min,seconds=x.tm_sec).total_seconds())

class TextNote(models.Model):
    BY_CHOICES = (
        ('patient', 'patient'),
        ('physician', 'physician'),
    )
    by = models.CharField(max_length=20, choices=BY_CHOICES)
    note = models.TextField()
    datetime = models.DateTimeField(auto_now_add=True)

        
    def get_dict(self):
        return instance_dict(self)

class Problem(MPTTModel):
    patient = models.ForeignKey(User)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children')
    problem_name = models.CharField(max_length=200)
    concept_id = models.CharField(max_length=20, blank=True)
    is_controlled = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    authenticated = models.BooleanField(default=False)
    notes = models.ManyToManyField(TextNote, blank=True)
    start_date = models.DateField(auto_now_add=True)
    
    def __unicode__(self):
        return '%s %s' % (self.patient, self.problem_name)

        
    def get_dict(self):
        return instance_dict(self)

    def generate_dict(self):
        obj_dict = {}
        obj_dict['id'] = self.id
        obj_dict['patient_id'] = self.patient.id
        obj_dict['concept_id'] = self.concept_id
        obj_dict['is_controlled']  = self.is_controlled
        obj_dict['is_active'] = self.is_active
        obj_dict['is_authenticated'] = self.authenticated
        obj_dict['problem_name'] = self.problem_name

        return obj_dict

class Goal(models.Model):
    patient = models.ForeignKey(User)
    problem = models.ForeignKey(Problem, null=True, blank=True)
    goal = models.TextField()
    is_controlled = models.BooleanField(default=False)
    accomplished = models.BooleanField(default=False)
    notes = models.ManyToManyField(TextNote, blank=True)
    start_date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%s %s' % (unicode(self.patient), unicode(self.problem))

        
    def get_dict(self):
        return instance_dict(self)

    def generate_dict(self):
        obj_dict = {}
        obj_dict['id'] = self.id
        obj_dict['patient_id'] = self.patient.id
        obj_dict['problem'] = unicode(self.problem)
        obj_dict['goal'] = self.goal
        obj_dict['is_controlled'] = self.is_controlled
        obj_dict['accomplished'] = self.accomplished
        obj_dict['start_date'] = str(self.start_date)

        return obj_dict


class ToDo(models.Model):
    patient = models.ForeignKey(User)
    problem = models.ForeignKey(Problem, null=True, blank=True)
    todo = models.TextField()
    accomplished = models.BooleanField(default=False)    
    notes = models.ManyToManyField(TextNote, blank=True)


    def __unicode__(self):
        return '%s' % (unicode(self.patient))

        
    def get_dict(self):
        return instance_dict(self)

    def generate_dict(self):
        obj_dict = {}
        obj_dict['patient_id'] = self.patient.id

        if self.problem:
            obj_dict['problem'] = self.problem.problem_name
        else:
            obj_dict['problem'] = 'None'

        obj_dict['todo'] = self.todo
        obj_dict['accomplished'] = self.accomplished

        return obj_dict

class Guideline(models.Model):
    concept_id = models.CharField(max_length=20, blank=True)
    guideline = models.TextField()
    reference_url = models.CharField(max_length=400, blank=True)

    def __unicode__(self):
        return '%s %s' % (self.concept_id, self.guideline)

         
    def get_dict(self):
        return instance_dict(self)
        
    def get_form(self):
        try:
            return GuidelineForm.objects.get(guideline=self).form
        except:
            return "[]"
        
class GuidelineForm(models.Model):
    guideline = models.OneToOneField(Guideline)
    form = models.TextField()
    
    def __unicode__(self):
        return self.guideline.__unicode__()
    
class PatientImage(models.Model):
    patient = models.ForeignKey(User)
    problem = models.ForeignKey(Problem, null=True, blank=True)
    image = models.ImageField(upload_to=get_path) 
    datetime = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%s' % (unicode(self.patient))
        
        
    def get_dict(self):
        return instance_dict(self)
        
class Sharing(models.Model):
    patient = models.ForeignKey(User, related_name='target_patient')
    other_patient = models.ForeignKey(User, related_name='other_patient')
    all = models.BooleanField(default=True)
    
    def __unicode__(self):
        return '%s %s' % (unicode(self.patient), unicode(self.other_patient))

        
    def get_dict(self):
        return instance_dict(self)
        
class Viewer(models.Model):
    patient = models.ForeignKey(User, related_name='viewed_patient')
    viewer = models.ForeignKey(User, related_name='viewer')
    datetime = models.DateTimeField(auto_now=True)
    tracking_id = models.CharField(max_length=20, blank=True) # for tracking open browser instances e.g. multiple tabs
    user_agent = models.CharField(max_length=200, blank=True) # user agent is type of browser/OS/version

        
    def get_dict(self):
        return instance_dict(self)
    
class ViewStatus(models.Model):
    patient = models.ForeignKey(User)
    status = models.TextField()
    
        
    def get_dict(self):
        return instance_dict(self)    

class ProblemRelationship(models.Model):
    source = models.ForeignKey(Problem, related_name="source")
    target = models.ForeignKey(Problem, related_name="target")
    
    def __unicode__(self):
        return "%s %s" % (unicode(self.source), unicode(self.target))
