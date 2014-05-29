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

class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)
    ROLE_CHOICES = (
        ('patient', 'patient'),
        ('physician', 'physician'),
        ('admin', 'admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='patient')
    data = models.TextField(blank=True) 
    cover_image = models.ImageField(upload_to='cover_image/', blank=True)
    portrait_image = models.ImageField(upload_to='cover_image/', blank=True)
    ROLE_CHOICES = (
        ('male', 'male'),
        ('female', 'female'),
    )
    sex = models.CharField(max_length=6, choices=SEX_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    
    def __unicode__(self):
        return '%s' % (self.user.get_full_name())
        
    def get_dict(self):
        return instance_dict(self)

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
    events = models.ManyToManyField('EncounterEvent')
    audio = models.FileField(upload_to=get_path, blank=True) 
    video = models.FileField(upload_to=get_path, blank=True)
    note = models.TextField(blank=True)
    
    def __unicode__(self):
        return 'Patient: %s Time: %s' % (self.patient.get_full_name(), self.physician.get_full_name())

        
    def get_dict(self):
        return instance_dict(self)

class EncounterEvent(models.Model):
    datetime = models.DateTimeField(auto_now_add=True)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    event = generic.GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return unicode(self.event)
        
        
    def get_dict(self):
        return instance_dict(self)
        
class EventSummary(models.Model):
    patient = models.ForeignKey(User)
    datetime = models.DateTimeField(auto_now_add=True)
    summary = models.TextField()

    def __unicode__(self):
        return '%s %s' % (unicode(self.patient), self.summary)

        
    def get_dict(self):
        return instance_dict(self)

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

class Guideline(models.Model):
    concept_id = models.CharField(max_length=20, blank=True)
    guideline = models.TextField()
    reference_url = models.CharField(max_length=400, blank=True)

    def __unicode__(self):
        return '%s %s' % (self.concept_id, self.guideline)

        
    def get_dict(self):
        return instance_dict(self)

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
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    item = generic.GenericForeignKey('content_type', 'object_id')
    relationship_to_patient = models.CharField(max_length=20, blank=True)
    relationship_to_patient_snomed = models.CharField(max_length=20, blank=True)
    relationship_to_other_patient = models.CharField(max_length=20, blank=True)
    relationship_to_other_patient_snomed = models.CharField(max_length=20, blank=True)
    
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
