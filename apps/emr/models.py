import os
import ast
from django.db import models
from django.contrib.auth.models import User
from mptt.models import MPTTModel, TreeForeignKey

from emr.managers import ObservationManager, ProblemManager, ProblemNoteManager

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


COMMON_PROBLEM_TYPE_CHOICES = (
    ('acute', 'Acute'),
    ('chronic', 'Chronic'), )


# UTILITIES
def get_path(instance, filename):
    try:
        return '%s/%s/%s' % (
            instance.patient.id, instance.problem.id, filename)
    except:
        return '%s/%s' % (instance.patient.id, filename)


class ListField(models.TextField):
    __metaclass__ = models.SubfieldBase
    description = "Stores a python list"

    def __init__(self, *args, **kwargs):
        super(ListField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if not value:
            value = []

        if isinstance(value, list):
            return value

        return ast.literal_eval(value)

    def get_prep_value(self, value):
        if value is None:
            return value

        return unicode(value)

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)

class MaritalStatus(models.Model):
    code = models.CharField(max_length=1, null=True, blank=True)
    display = models.CharField(max_length=20, null=True, blank=True)
    definition = models.CharField(max_length=64, null=True, blank=True)


class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name="profile")
    role = models.CharField(
        max_length=10, choices=ROLE_CHOICES, default='patient')
    data = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='cover_image/', blank=True)
    portrait_image = models.ImageField(upload_to='cover_image/', blank=True)
    summary = models.TextField(blank=True)
    sex = models.CharField(max_length=6, choices=SEX_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    deceased_date = models.DateTimeField(null=True, blank=True)
    marital_status = models.ForeignKey(MaritalStatus, null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    note = models.TextField(null=True, blank=True)

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

    is_favorite = models.BooleanField(default=False)
    name_favorite = models.TextField(null=True, blank=True)

    timestamp = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        return unicode(self.summary)

    def video_seconds(self):
        if self.timestamp:
            time_diff = self.timestamp - self.encounter.starttime
        else:
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


class ProblemLabel(models.Model):
    name = models.TextField(null=True, blank=True)
    css_class = models.TextField(null=True, blank=True)
    author = models.ForeignKey(User, null=True, blank=True, related_name="problem_label_author")
    patient = models.ForeignKey(User, null=True, blank=True, related_name="problem_label_patient")

    def __unicode__(self):
        return '%s' % (unicode(self.name))


class Problem(MPTTModel):
    patient = models.ForeignKey(User)
    parent = TreeForeignKey(
        'self', null=True, blank=True, related_name='children')
    problem_name = models.CharField(max_length=200)
    concept_id = models.CharField(max_length=20, blank=True, null=True)
    is_controlled = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    authenticated = models.BooleanField(default=False)
    start_date = models.DateField(auto_now_add=True)
    start_time = models.TimeField(auto_now_add=True, null=True, blank=True)
    labels = models.ManyToManyField(ProblemLabel, blank=True)
    old_problem_name = models.CharField(max_length=200, blank=True, null=True)

    objects = ProblemManager()

    def __unicode__(self):
        return '%s %s' % (self.patient, self.problem_name)


class SharingPatient(models.Model):
    sharing = models.ForeignKey(User, related_name='patient_sharing')
    shared = models.ForeignKey(User, related_name='patient_shared')
    problems = models.ManyToManyField(Problem, blank=True, related_name="sharing_problems")


class ProblemOrder(models.Model):
    patient = models.ForeignKey(User, null=True, blank=True, related_name="patient_problem_order")
    user = models.ForeignKey(User, null=True, blank=True, related_name="user_problem_order")
    order = ListField(null=True, blank=True)

    def __unicode__(self):
        return '%s' % (unicode(self.user.username))


class ProblemSegment(models.Model):
    problem = models.ForeignKey(Problem, related_name='problem_segment')
    is_controlled = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    authenticated = models.BooleanField(default=False)
    event_id = models.BigIntegerField(null=True, blank=True)
    start_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)

    class Meta:
        ordering = ('start_date', 'start_time', )

    def __unicode__(self):
        return '%s segment %s' % (self.problem.problem_name, self.start_date)


class ProblemActivity(models.Model):
    problem = models.ForeignKey(Problem)
    activity = models.TextField()
    author = models.ForeignKey(UserProfile, null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    is_input_type = models.BooleanField(default=False)
    is_output_type = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_on']


class ProblemNote(models.Model):
    author = models.ForeignKey(UserProfile, null=True, blank=True)
    problem = models.ForeignKey(Problem, null=True, blank=True)
    note = models.TextField()
    note_type = models.CharField(choices=NOTE_TYPE_CHOICES, max_length=50)
    created_on = models.DateTimeField(auto_now_add=True)

    objects = ProblemNoteManager()

    def __unicode__(self):
        return "%s %s" % (self.author, self.note)


class LabeledProblemList(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, related_name="label_problem_list_user")
    patient = models.ForeignKey(User, null=True, blank=True, related_name="label_problem_list_patient")
    labels = models.ManyToManyField(ProblemLabel, blank=True)
    name = models.TextField()
    problem_list = ListField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return '%s' % (unicode(self.name))


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


class Label(models.Model):
    name = models.TextField(null=True, blank=True)
    css_class = models.TextField(null=True, blank=True)
    author = models.ForeignKey(User, null=True, blank=True, related_name="label_author")
    is_all = models.BooleanField(default=False)

    def __unicode__(self):
        return '%s' % (unicode(self.name))


class ToDo(models.Model):
    patient = models.ForeignKey(User, null=True, blank=True, related_name="todo_patient")
    user = models.ForeignKey(User, null=True, blank=True, related_name="todo_owner")
    problem = models.ForeignKey(Problem, null=True, blank=True)
    observation = models.ForeignKey("Observation", null=True, blank=True, related_name="observation_todos")
    todo = models.TextField()
    accomplished = models.BooleanField(default=False)
    notes = models.ManyToManyField(TextNote, blank=True)
    due_date = models.DateField(blank=True, null=True)
    order = models.BigIntegerField(null=True, blank=True)
    members = models.ManyToManyField(UserProfile, blank=True)
    labels = models.ManyToManyField(Label, blank=True)
    created_on = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __unicode__(self):
        return '%s' % (unicode(self.todo))


class TaggedToDoOrder(models.Model):
    user = models.ForeignKey(User, null=True, blank=True)
    todo = models.ForeignKey(ToDo, null=True, blank=True)
    order = models.BigIntegerField(null=True, blank=True)

    def __unicode__(self):
        return '%s' % (unicode(self.todo.todo))


class LabeledToDoList(models.Model):
    user = models.ForeignKey(User)
    labels = models.ManyToManyField(Label, blank=True)
    name = models.TextField()
    todo_list = ListField(null=True, blank=True)
    expanded = ListField(null=True, blank=True)

    def __unicode__(self):
        return '%s' % (unicode(self.name))


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


class ToDoComment(models.Model):
    todo = models.ForeignKey(ToDo, related_name="comments")
    user = models.ForeignKey(User)
    comment = models.TextField(null=True, blank=True)
    datetime = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '%s' % (unicode(self.todo.todo))


class ToDoAttachment(models.Model):
    todo = models.ForeignKey(ToDo, related_name="attachments")
    attachment = models.FileField(upload_to='attachments/', blank=True)
    datetime = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User)

    def __unicode__(self):
        return '%s' % (unicode(self.attachment.path))

    def filename(self):
        return os.path.basename(self.attachment.name)

    def file_extension(self):
        name, extension = os.path.splitext(self.attachment.name)
        extension = extension.replace('.', '')
        return extension.upper()

    def file_extension_lower(self):
        name, extension = os.path.splitext(self.attachment.name)
        extension = extension.replace('.', '')
        return extension

    def is_image(self):
        extensions = ['jpg', 'png', 'jpeg']
        if self.file_extension_lower() in extensions:
            return True
        return False


class EncounterTodoRecord(models.Model):
    encounter = models.ForeignKey(
        Encounter, related_name='encounter_todo_records')
    todo = models.ForeignKey(
        ToDo, related_name='todo_encounter_records')

    def __unicode__(self):
        return "%s %s" % (unicode(self.encounter), unicode(self.todo))


class TodoActivity(models.Model):
    todo = models.ForeignKey(ToDo)
    activity = models.TextField()
    author = models.ForeignKey(UserProfile, null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    comment = models.ForeignKey(ToDoComment, null=True, blank=True)
    attachment = models.ForeignKey(ToDoAttachment, null=True, blank=True)

    class Meta:
        ordering = ['-created_on']


class Observation(models.Model):
    status = models.CharField(max_length=16)
    category = models.CharField(max_length=45, null=True, blank=True)
    code = models.CharField(max_length=10)
    subject = models.ForeignKey(UserProfile, related_name='observation_subjects')
    encounter = models.ForeignKey(UserProfile, null=True, blank=True, related_name='observation_encounters')
    performer = models.ForeignKey(UserProfile, null=True, blank=True, related_name='observation_performers')
    author = models.ForeignKey(UserProfile, null=True, blank=True, related_name='observation_authors')
    effective_datetime = models.DateTimeField(null=True, blank=True)
    value_quantity = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    value_codeableconcept = models.CharField(max_length=40, null=True, blank=True)
    value_string = models.TextField(null=True, blank=True)
    value_unit = models.CharField(max_length=45, null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    problem = models.ForeignKey(Problem, related_name='problem_observations')
    todo_past_six_months = models.BooleanField(default=False)
    patient_refused_A1C = models.BooleanField(default=False)

    objects = ObservationManager()

    class Meta:
        ordering = ['-created_on']


class ObservationComponent(models.Model):
    status = models.CharField(max_length=16)
    observation = models.ForeignKey(Observation, related_name='observation_components')
    component_code = models.CharField(max_length=10)
    value_quantity = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    value_codeableconcept = models.CharField(max_length=40, null=True, blank=True)
    value_string = models.TextField(null=True, blank=True)
    value_unit = models.CharField(max_length=45, null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    effective_datetime = models.DateTimeField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    author = models.ForeignKey(UserProfile, null=True, blank=True, related_name='observation_component_authors')

    class Meta:
        ordering = ['effective_datetime', 'created_on']


class Country(models.Model):
    iso3 = models.CharField(max_length=3)
    iso_num = models.CharField(max_length=3)
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return "%s" % (self.name)


class State(models.Model):
    country = models.ForeignKey(Country, related_name='country_states')
    code = models.CharField(max_length=2)
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return "%s" % (self.name)


class City(models.Model):
    state = models.ForeignKey(State, related_name='state_cities')
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return "%s" % (self.name)


class Address(models.Model):
    line1 = models.CharField(max_length=50)
    line2 = models.CharField(max_length=50)
    city = models.ForeignKey(City, related_name='city_addresses')
    zip = models.CharField(max_length=6)
    zip4 = models.CharField(max_length=4, null=True, blank=True)
    lat = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    lon = models.DecimalField(max_digits=11, decimal_places=4, null=True, blank=True)
    county = models.CharField(max_length=30, null=True, blank=True)


class TelecomSystem(models.Model):
    code = models.CharField(max_length=5, primary_key=True)
    display = models.CharField(max_length=50)
    definition = models.TextField()

    def __unicode__(self):
        return "%s" % (self.code)


class Telecom(models.Model):
    system_code = models.CharField(max_length=5)
    value = models.TextField()

    def __unicode__(self):
        return "%s" % (self.system_code)


class AddressType(models.Model):
    code = models.CharField(max_length=8, primary_key=True)
    display = models.CharField(max_length=17)
    definition = models.CharField(max_length=51)

    def __unicode__(self):
        return "%s" % (self.code)


class AddressUse(models.Model):
    code = models.CharField(max_length=4, primary_key=True)
    display = models.CharField(max_length=15)
    definition = models.CharField(max_length=90)

    def __unicode__(self):
        return "%s" % (self.code)


class UserTelecom(models.Model):
    user = models.ForeignKey(User, related_name='user_telecoms')
    telecom = models.ForeignKey(Telecom, related_name='telecom_users')
    use_code = models.CharField(max_length=6)
    rank = models.PositiveIntegerField(null=True, blank=True)
    start = models.DateField(null=True, blank=True)
    end = models.DateField(null=True, blank=True)


class UserAddress(models.Model):
    user = models.ForeignKey(User, related_name='user_addresses')
    address = models.ForeignKey(Address, related_name='address_users')
    type_code = models.ForeignKey(AddressType, related_name='type_code_user_address')
    use_code = models.ForeignKey(AddressUse, related_name='use_code_user_address')
    start = models.DateField(null=True, blank=True)
    end = models.DateField(null=True, blank=True)


class ObservationTextNote(models.Model):
    observation = models.ForeignKey(Observation, related_name='observation_notes')
    author = models.ForeignKey(UserProfile, null=True, blank=True)
    note = models.TextField()
    datetime = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s" % (self.note)


class ObservationComponentTextNote(models.Model):
    observation_component = models.ForeignKey(ObservationComponent, related_name='observation_component_notes')
    author = models.ForeignKey(UserProfile, null=True, blank=True)
    note = models.TextField()
    datetime = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s" % (self.note)


class CommonProblem(models.Model):
    author = models.ForeignKey(User, null=True, blank=True, related_name="common_problem_author")
    problem_name = models.CharField(max_length=200)
    concept_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    problem_type = models.CharField(max_length=10, choices=COMMON_PROBLEM_TYPE_CHOICES, default='acute')
