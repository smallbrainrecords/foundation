from django.db import models
from django.contrib.auth.models import User
from mptt.models import MPTTModel, TreeForeignKey


# DATA
ROLE_CHOICES = (
    ('patient', 'Patient'),
    ('physician', 'Physician'),
    ('mid-level', 'Mid Level PA/NP'),
    ('nurse', 'Nurse'),
    ('secretary', 'Secretary'),
    ('admin', 'Admin'),)


SEX_CHOICES = (
    ('male', 'Male'),
    ('female', 'Female'),)


BY_CHOICES = (
    ('patient', 'patient'),
    ('physician', 'physician'), )


NOTE_TYPE_CHOICES = (
    ('wiki', 'Wiki'),
    ('history', 'History'), )


# UTILITIES
def get_path(instance, filename):
    try:
        return '%s/%s/%s' % (
            instance.patient.id, instance.problem.id, filename)
    except:
        return '%s/%s' % (instance.patient.id, filename)


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    role = models.CharField(
        max_length=10, choices=ROLE_CHOICES, default='patient')
    data = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='cover_image/', blank=True)
    portrait_image = models.ImageField(upload_to='cover_image/', blank=True)
    summary = models.TextField(blank=True)
    sex = models.CharField(max_length=6, choices=SEX_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)

    def __unicode__(self):
        return '%s' % (self.user.get_full_name())


# Many To Many Relation
class PatientController(models.Model):
    patient = models.ForeignKey(User, related_name='patient_physicians')
    physician = models.ForeignKey(User, related_name='physician_patients')
    author = models.BooleanField(default=False)


class PhysicianTeam(models.Model):
    # Need to add  save_admin to check if member is physician
    physician = models.ForeignKey(User, related_name='physician_helpers')
    member = models.ForeignKey(User, related_name='user_leaders')


class AccessLog(models.Model):
    user = models.ForeignKey(User)
    datetime = models.DateTimeField(auto_now_add=True)
    summary = models.TextField()

    def __unicode__(self):
        return '%s %s %s' % (self.user.username, self.datetime, self.summary)


class Encounter(models.Model):
    physician = models.ForeignKey(User, related_name="physician_encounters")
    patient = models.ForeignKey(User, related_name="patient_encounters")
    starttime = models.DateTimeField(auto_now_add=True)
    stoptime = models.DateTimeField(null=True, blank=True)
    audio = models.FileField(upload_to=get_path, blank=True)
    video = models.FileField(upload_to=get_path, blank=True)
    note = models.TextField(blank=True)

    def __unicode__(self):
        return 'Patient: %s Time: %s' % (
            self.patient.get_full_name(), self.physician.get_full_name())

    def is_active(self):
        if self.stoptime:
            return False
        else:
            return True

    def duration(self):
        if self.stoptime:
            return str(self.stoptime - self.starttime)
        else:
            return 0


class EncounterEvent(models.Model):
    encounter = models.ForeignKey(
        Encounter, related_name='encounter_events', null=True, blank=True)

    datetime = models.DateTimeField(auto_now_add=True)
    summary = models.TextField(default='')

    def __unicode__(self):
        return unicode(self.summary)

    def video_seconds(self):
        time_diff = self.datetime - self.encounter.starttime
        x = int(time_diff.total_seconds())
        return x

    def video_timestamp(self):
        seconds = self.video_seconds()
        h = seconds // 60
        s = seconds % 60
        if s < 10:
            s = '0' + str(s)
        return '%s:%s' % (h, s)


class TextNote(models.Model):

    author = models.ForeignKey(UserProfile, null=True, blank=True)
    by = models.CharField(max_length=20, choices=BY_CHOICES)
    note = models.TextField()
    datetime = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s %s" % (self.by, self.note)


class Problem(MPTTModel):
    patient = models.ForeignKey(User)
    parent = TreeForeignKey(
        'self', null=True, blank=True, related_name='children')
    problem_name = models.CharField(max_length=200)
    concept_id = models.CharField(max_length=20, blank=True)
    is_controlled = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    authenticated = models.BooleanField(default=False)
    start_date = models.DateField(auto_now_add=True)

    def __unicode__(self):
        return '%s %s' % (self.patient, self.problem_name)


class ProblemActivity(models.Model):
    problem = models.ForeignKey(Problem)
    activity = models.TextField()
    author = models.ForeignKey(UserProfile, null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_on']


class ProblemNote(models.Model):
    author = models.ForeignKey(UserProfile, null=True, blank=True)
    problem = models.ForeignKey(Problem, null=True, blank=True)
    note = models.TextField()
    note_type = models.CharField(choices=NOTE_TYPE_CHOICES, max_length=50)
    created_on = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s %s" % (self.author, self.note)


class Goal(models.Model):
    patient = models.ForeignKey(User)
    problem = models.ForeignKey(Problem, null=True, blank=True)
    goal = models.TextField()
    is_controlled = models.BooleanField(default=False)
    accomplished = models.BooleanField(default=False)
    notes = models.ManyToManyField(TextNote, blank=True)
    start_date = models.DateField(auto_now_add=True)

    def __unicode__(self):
        return '%s %s' % (unicode(self.patient), unicode(self.problem))


class ToDo(models.Model):
    patient = models.ForeignKey(User)
    problem = models.ForeignKey(Problem, null=True, blank=True)
    todo = models.TextField()
    accomplished = models.BooleanField(default=False)
    notes = models.ManyToManyField(TextNote, blank=True)

    def __unicode__(self):
        return '%s' % (unicode(self.patient))


class Guideline(models.Model):
    concept_id = models.CharField(max_length=20, blank=True)
    guideline = models.TextField()
    reference_url = models.CharField(max_length=400, blank=True)

    def __unicode__(self):
        return '%s %s' % (self.concept_id, self.guideline)

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


class Sharing(models.Model):
    patient = models.ForeignKey(User, related_name='target_patient')
    other_patient = models.ForeignKey(User, related_name='other_patient')
    all = models.BooleanField(default=True)

    def __unicode__(self):
        return '%s %s' % (unicode(self.patient), unicode(self.other_patient))


class Viewer(models.Model):
    patient = models.ForeignKey(User, related_name='viewed_patient')
    viewer = models.ForeignKey(User, related_name='viewer')
    datetime = models.DateTimeField(auto_now=True)
    # for tracking open browser instances e.g. multiple tabs
    tracking_id = models.CharField(max_length=20, blank=True)
    # user agent is type of browser/OS/version
    user_agent = models.CharField(max_length=200, blank=True)


class ViewStatus(models.Model):
    patient = models.ForeignKey(User)
    status = models.TextField()


class ProblemRelationship(models.Model):
    source = models.ForeignKey(Problem, related_name="source")
    target = models.ForeignKey(Problem, related_name="target")

    def __unicode__(self):
        return "%s %s" % (unicode(self.source), unicode(self.target))


class EncounterProblemRecord(models.Model):
    encounter = models.ForeignKey(
        Encounter, related_name='encounter_problem_records')
    problem = models.ForeignKey(
        Problem, related_name='problem_encounter_records')

    def __unicode__(self):
        return "%s %s" % (unicode(self.encounter), unicode(self.problem))
