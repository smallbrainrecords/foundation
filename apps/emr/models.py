"""
Copyright (c) Small Brain Records 2014-2018 Kevin Perdue, James Ryan with contributors Timothy Clemens and Dinh Ngoc Anh

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""
import ast
import mimetypes
import os

import reversion
from django.contrib.auth.models import User
from django.db import models
from emr.managers import (
    AOneCManager,
    ColonCancerScreeningManager,
    ColonCancerStudyManager,
    EncounterManager,
    ProblemManager,
    ProblemNoteManager,
    TodoManager,
)
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
    ('physician', 'physician'),)

NOTE_TYPE_CHOICES = (
    ('wiki', 'Wiki'),
    ('history', 'History'),)

COMMON_PROBLEM_TYPE_CHOICES = (
    ('acute', 'Acute'),
    ('chronic', 'Chronic'),)

RISK_CHOICES = (
    ('normal', 'Normal'),
    ('high', 'High'),)

# Patient target INR goal(used within INR widget)
TARGET_CHOICES = (
    (1, '2-3'),
    (0, '2.5-3.5')
)

# Place where the item(Todo, Note, Value...) is generated
BELONG_TO = (
    (0, ''),
    (1, 'inr_widget')
)

# Observation type
OBSERVATION_TYPES = [
    {
        'name': 'a1c',
        'loinc_code': '4548-4',
    },
    {
        'name': 'heart rate',
        'unit': [
            'bpm',
        ],
        'loinc_code': '8867-4',
    },
    {
        'name': 'blood pressure',
        'unit': [
            'mmHg',
        ],
        'loinc_code': '85354-9',
        'components': [
            {
                'name': 'systolic',
                'loinc_code': '8480-6',
            },
            {
                'name': 'diastolic',
                'loinc_code': '8462-4',
            },
        ],
    },
    {
        'name': 'respiratory rate',
        'unit': [
            'breaths/min',
        ],
        'loinc_code': '9279-1',
    },
    {
        'name': 'body temperature',
        'unit': [
            'F',
            'C',
        ],
        'loinc_code': '8310-5',
    },
    {
        'name': 'height',
        'unit': [
            'in',
            'ft',
            'cm',
        ],
        'loinc_code': '8302-2',
    },
    {
        'name': 'weight',
        'unit': [
            'lb',
            'kg',
        ],
        'loinc_code': '3141-9',
    },
    {
        'name': 'body mass index',
        'unit': [
            'bmi',
        ],
        'loinc_code': '39156-5',
    },
    {
        'name': 'oxygen saturation',
        'unit': [
            '%',
        ],
        'loinc_code': '59408-5',
    },
    {
        'name': 'PHQ-2',
        'loinc_code': '55757-9',
        'unit': [],
        'color': '#FFFF00'
    }
]

VIEW_STATUS = (
    (0, 'New'),
    (1, 'Seen'),
    (2, 'Viewed')
)

RECORDER_STATUS = (
    (0, 'isRecording'),
    (1, 'isPaused'),
    (2, 'isStopped')
)
# Medication concept id set used on INR related problem
MEDICATION_BLEEDING_RISK = {375383004, 375379004, 375378007, 319735007, 375374009,
                            319734006, 375380001, 375375005, 319733000, 319736008}


# UTILITIES
def get_path(instance, filename):
    try:
        return '%s/%s/%s' % (
            instance.patient.id, instance.problem.id, filename)
    except:
        return '%s/%s' % (instance.patient.id, filename)


def set_document_path(instance, filename):
    if instance.patient is not None:
        return "{0}/documents/{1}".format(instance.patient.id, filename)
    else:
        return "documents/{0}".format(filename)


class ListField(models.TextField):
    description = "Stores a python list"

    def __init__(self, *args, **kwargs):
        super(ListField, self).__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection, context = None):
        if not value:
            value = []

        if isinstance(value, list):
            return value

        return ast.literal_eval(value)

    def to_python(self, value):
        if not value:
            value = []

        if isinstance(value, list):
            return value

        return ast.literal_eval(value)

    def get_prep_value(self, value):
        if value is None:
            return value

        return value

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)


# Resources https://www.hl7.org/fhir/resourcelist.html

class MaritalStatus(models.Model):
    code = models.CharField(max_length=1, null=True, blank=True)
    display = models.CharField(max_length=20, null=True, blank=True)
    definition = models.CharField(max_length=64, null=True, blank=True)


class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name="profile", on_delete=models.DO_NOTHING)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='patient')
    data = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='cover_image/', default='/static/images/cover.png')
    portrait_image = models.ImageField(upload_to='cover_image/', default='/static/images/avatar.png')
    summary = models.TextField(blank=True)
    sex = models.CharField(max_length=6, choices=SEX_CHOICES, blank=True)
    date_of_birth = models.DateTimeField(null=True, blank=True)
    deceased_date = models.DateTimeField(null=True, blank=True)
    marital_status = models.ForeignKey(MaritalStatus, null=True, blank=True, on_delete=models.DO_NOTHING)
    phone_number = models.CharField(max_length=20, blank=True)
    note = models.TextField(null=True, blank=True)
    active_reason = models.TextField(null=True, blank=True)
    inr_target = models.PositiveIntegerField(choices=TARGET_CHOICES, default=1)
    last_access_tagged_todo = models.DateTimeField(null=True, blank=True)
    insurance_medicare = models.BooleanField(default=False)
    insurance_note = models.TextField(blank=True)
    weight_updated_date = models.DateTimeField(null=True, blank=True)
    height_updated_date = models.DateTimeField(null=True, blank=True)
    height_changed_first_time = models.BooleanField(default=False)


    def __unicode__(self):
        return '%s' % (self.user.get_full_name())


# Many To Many Relation
class PatientController(models.Model):
    patient = models.ForeignKey(User, related_name='patient_physicians', on_delete=models.DO_NOTHING)
    physician = models.ForeignKey(User, related_name='physician_patients', on_delete=models.DO_NOTHING)
    author = models.BooleanField(default=False)


class PhysicianTeam(models.Model):
    # Need to add  save_admin to check if member is physician
    physician = models.ForeignKey(User, related_name='physician_helpers', on_delete=models.DO_NOTHING)
    member = models.ForeignKey(User, related_name='user_leaders', on_delete=models.DO_NOTHING)


class AccessLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    datetime = models.DateTimeField(auto_now_add=True)
    summary = models.TextField()

    def __unicode__(self):
        return '%s %s %s' % (self.user.username, self.datetime, self.summary)


class Encounter(models.Model):
    physician = models.ForeignKey(User, related_name="physician_encounters", on_delete=models.DO_NOTHING)
    patient = models.ForeignKey(User, related_name="patient_encounters", on_delete=models.DO_NOTHING)
    starttime = models.DateTimeField(auto_now_add=True)
    stoptime = models.DateTimeField(null=True, blank=True)
    audio = models.FileField(upload_to=get_path, blank=True)
    audio_played_count = models.IntegerField(default=0)
    recorder_status = models.IntegerField(choices=RECORDER_STATUS, default=0)
    video = models.FileField(upload_to=get_path, blank=True)
    note = models.TextField(blank=True)
    # deprecated should be loaded dynamically instead of storing in specific table
    encounter_document = models.ManyToManyField('ObservationValue', through='EncounterObservationValue')

    objects = EncounterManager()

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
            # Ignore microsecond part, min to seond
            return str(self.stoptime.replace(microsecond=0) - self.starttime.replace(microsecond=0))
        else:
            return 0


class EncounterEvent(models.Model):
    encounter = models.ForeignKey(Encounter, related_name='encounter_events', null=True, blank=True, on_delete=models.DO_NOTHING)

    datetime = models.DateTimeField(auto_now_add=True)
    summary = models.TextField(default='')

    is_favorite = models.BooleanField(default=False)
    name_favorite = models.TextField(null=True, blank=True)

    timestamp = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        return self.summary

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


# @Deprecated
class TextNote(models.Model):
    author = models.ForeignKey(User, null=True, blank=True, on_delete=models.DO_NOTHING)
    by = models.CharField(max_length=20, choices=BY_CHOICES)
    note = models.TextField()
    datetime = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s %s" % (self.by, self.note)


class ProblemLabel(models.Model):
    name = models.TextField(null=True, blank=True)
    css_class = models.TextField(null=True, blank=True)
    author = models.ForeignKey(User, null=True, blank=True, related_name="problem_label_author", on_delete=models.DO_NOTHING)
    patient = models.ForeignKey(User, null=True, blank=True, related_name="problem_label_patient", on_delete=models.DO_NOTHING)

    def __unicode__(self):
        return self.name


class Problem(MPTTModel):
    patient = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.DO_NOTHING)
    problem_name = models.CharField(max_length=200)
    concept_id = models.CharField(max_length=20, blank=True, null=True)
    is_controlled = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    authenticated = models.BooleanField(default=False)
    start_date = models.DateTimeField(auto_now_add=True)
    start_time = models.TimeField(auto_now_add=True, null=True, blank=True)
    old_problem_name = models.CharField(max_length=200, blank=True, null=True)

    labels = models.ManyToManyField(ProblemLabel, blank=True)
    medications = models.ManyToManyField('Medication', through='MedicationPinToProblem')
    observations = models.ManyToManyField('Observation', through='ObservationPinToProblem')

    objects = ProblemManager()

    def __unicode__(self):
        return '%s %s' % (self.patient, self.problem_name)


class SharingPatient(models.Model):
    sharing = models.ForeignKey(User, related_name='patient_sharing', on_delete=models.DO_NOTHING)
    shared = models.ForeignKey(User, related_name='patient_shared', on_delete=models.DO_NOTHING)
    problems = models.ManyToManyField(Problem, blank=True, related_name="sharing_problems")
    is_my_story_shared = models.BooleanField(default=True)


class ProblemOrder(models.Model):
    patient = models.ForeignKey(User, null=True, blank=True, related_name="patient_problem_order", on_delete=models.DO_NOTHING)
    user = models.ForeignKey(User, null=True, blank=True, related_name="user_problem_order", on_delete=models.DO_NOTHING)
    order = ListField(null=True, blank=True)

    def __unicode__(self):
        return self.user.username


class ProblemSegment(models.Model):
    problem = models.ForeignKey(Problem, related_name='problem_segment', on_delete=models.DO_NOTHING)
    is_controlled = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    authenticated = models.BooleanField(default=False)
    event_id = models.BigIntegerField(null=True, blank=True)
    start_date = models.DateTimeField()
    start_time = models.TimeField(null=True, blank=True)

    class Meta:
        ordering = ('start_date', 'start_time',)

    def __unicode__(self):
        return '%s segment %s' % (self.problem.problem_name, self.start_date)


class ProblemActivity(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.DO_NOTHING)
    author = models.ForeignKey(User, null=True, blank=True, on_delete=models.DO_NOTHING)
    activity = models.TextField()
    is_input_type = models.BooleanField(default=False)
    is_output_type = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_on']


class ProblemNote(models.Model):
    author = models.ForeignKey(User, null=True, blank=True, on_delete=models.DO_NOTHING)
    problem = models.ForeignKey(Problem, null=True, blank=True, on_delete=models.DO_NOTHING)
    note = models.TextField()
    note_type = models.CharField(choices=NOTE_TYPE_CHOICES, max_length=50)
    created_on = models.DateTimeField(auto_now_add=True)

    objects = ProblemNoteManager()

    def __unicode__(self):
        return "%s %s" % (self.author, self.note)


class LabeledProblemList(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, related_name="label_problem_list_user", on_delete=models.DO_NOTHING)
    patient = models.ForeignKey(User, null=True, blank=True, related_name="label_problem_list_patient", on_delete=models.DO_NOTHING)
    labels = models.ManyToManyField(ProblemLabel, blank=True)
    name = models.TextField()
    problem_list = ListField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.name


class Goal(models.Model):
    patient = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    problem = models.ForeignKey(Problem, null=True, blank=True, on_delete=models.DO_NOTHING)
    goal = models.TextField()
    is_controlled = models.BooleanField(default=False)
    accomplished = models.BooleanField(default=False)
    notes = models.ManyToManyField(TextNote, blank=True)
    start_date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return f'{self.patient} {self.problem}'


class Label(models.Model):
    name = models.TextField(null=True, blank=True)
    css_class = models.TextField(null=True, blank=True)
    author = models.ForeignKey(User, null=True, blank=True, related_name="label_author", on_delete=models.DO_NOTHING)
    is_all = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name


class ToDo(models.Model):
    """
    CORE MODELS \n
    The task or 'todo' is a functional unit of care.
    Tasks are typically more discrete or focused than goals:
    changing a medication, getting some blood-work, starting physical therapy, checking blood pressure at home ...
    Tasks can be associated with a problem but are not required to have this association.
    Tasks are accomplished or not (true or false).
    Tasks have the capacity to be commented on by users.
    Tasks can be assigned to clinical staff of the care team.
    Tasks can have a due date.
    Tasks can have media files attached to them.
    Tasks that are associated with a problem are part of that problem's activity log.
    Tasks that are added or accomplished during an encounter are timestamped for that encounter and create annotations for that encounters media file.
    """
    todo = models.TextField()
    accomplished = models.BooleanField(default=False)
    due_date = models.DateTimeField(blank=True, null=True)
    order = models.BigIntegerField(null=True, blank=True)  # Position in normal todo list

    user = models.ForeignKey(User, null=True, blank=True, related_name="todo_owner", on_delete=models.DO_NOTHING)  # Author
    patient = models.ForeignKey(User, null=True, blank=True, related_name="todo_patient", on_delete=models.DO_NOTHING)
    labels = models.ManyToManyField(Label, blank=True)
    a1c = models.ForeignKey("AOneC", null=True, blank=True, related_name="a1c_todos", on_delete=models.DO_NOTHING)
    problem = models.ForeignKey(Problem, null=True, blank=True, on_delete=models.DO_NOTHING)
    colon_cancer = models.ForeignKey("ColonCancerScreening", null=True, blank=True, related_name="colon_cancer_todos", on_delete=models.DO_NOTHING)
    notes = models.ManyToManyField(TextNote, blank=True)  # aka comment should 1-n relation
    members = models.ManyToManyField(User, through="TaggedToDoOrder")
    medication = models.ForeignKey("Medication", null=True, on_delete=models.DO_NOTHING)

    created_at = models.PositiveIntegerField(choices=BELONG_TO, default=0)  # Place where todo is generated -> removed
    created_on = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    objects = TodoManager()

    def __unicode__(self):
        return self.todo


class TaggedToDoOrder(models.Model):
    order = models.BigIntegerField(null=True, blank=True)
    status = models.IntegerField(choices=VIEW_STATUS, default=0)
    todo = models.ForeignKey(ToDo, null=True, blank=True, on_delete=models.DO_NOTHING)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.DO_NOTHING)
    created_on = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __unicode__(self):
        return self.todo.todo


class LabeledToDoList(models.Model):
    name = models.TextField()
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)  # author
    labels = models.ManyToManyField(Label, blank=True)
    private = models.BooleanField(default=1)  # 1 is save just for me, 0: is save for all user
    todo_list = ListField(null=True, blank=True)
    expanded = ListField(null=True, blank=True)

    def __unicode__(self):
        return self.name


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
    guideline = models.OneToOneField(Guideline, on_delete=models.DO_NOTHING)
    form = models.TextField()

    def __unicode__(self):
        return self.guideline.__unicode__()


class PatientImage(models.Model):
    patient = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    problem = models.ForeignKey(Problem, null=True, blank=True, on_delete=models.DO_NOTHING)
    image = models.ImageField(upload_to=get_path)
    datetime = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.patient


class Sharing(models.Model):
    patient = models.ForeignKey(User, related_name='target_patient', on_delete=models.DO_NOTHING)
    other_patient = models.ForeignKey(User, related_name='other_patient', on_delete=models.DO_NOTHING)
    all = models.BooleanField(default=True)

    def __unicode__(self):
        return f'{self.patient} {self.other_patient}'


class Viewer(models.Model):
    patient = models.ForeignKey(User, related_name='viewed_patient', on_delete=models.DO_NOTHING)
    viewer = models.ForeignKey(User, related_name='viewer', on_delete=models.DO_NOTHING)
    datetime = models.DateTimeField(auto_now=True)
    # for tracking open browser instances e.g. multiple tabs
    tracking_id = models.CharField(max_length=20, blank=True)
    # user agent is type of browser/OS/version
    user_agent = models.CharField(max_length=200, blank=True)


class ViewStatus(models.Model):
    patient = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    status = models.TextField()


class ProblemRelationship(models.Model):
    source = models.ForeignKey(Problem, related_name="source", on_delete=models.DO_NOTHING)
    target = models.ForeignKey(Problem, related_name="target", on_delete=models.DO_NOTHING)

    def __unicode__(self):
        return f'{self.source} {self.target}'


class EncounterProblemRecord(models.Model):
    encounter = models.ForeignKey(
        Encounter, related_name='encounter_problem_records', on_delete=models.DO_NOTHING)
    problem = models.ForeignKey(
        Problem, related_name='problem_encounter_records', on_delete=models.DO_NOTHING)

    def __unicode__(self):
        return f'{self.encounter} {self.problem}'


class ToDoComment(models.Model):
    todo = models.ForeignKey(ToDo, related_name="comments", on_delete=models.DO_NOTHING)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    comment = models.TextField(null=True, blank=True)
    datetime = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.todo.todo


class ToDoAttachment(models.Model):
    todo = models.ForeignKey(ToDo, related_name="attachments", on_delete=models.DO_NOTHING)
    attachment = models.FileField(upload_to='attachments/', blank=True)
    datetime = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)

    def __unicode__(self):
        return self.attachment.path

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
        Encounter, related_name='encounter_todo_records', on_delete=models.DO_NOTHING)
    todo = models.ForeignKey(
        ToDo, related_name='todo_encounter_records', on_delete=models.DO_NOTHING)

    def __unicode__(self):
        return f'{self.encounter} {self.todo}'


class TodoActivity(models.Model):
    todo = models.ForeignKey(ToDo, on_delete=models.DO_NOTHING)
    author = models.ForeignKey(User, null=True, blank=True, on_delete=models.DO_NOTHING)
    comment = models.ForeignKey(ToDoComment, null=True, blank=True, on_delete=models.DO_NOTHING)
    attachment = models.ForeignKey(ToDoAttachment, null=True, blank=True, on_delete=models.DO_NOTHING)
    activity = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_on']


class Observation(models.Model):
    """
    https://www.hl7.org/fhir/observation.html
    """
    name = models.CharField(max_length=255, null=True, blank=True)
    # TODO: Check for deprecation
    status = models.CharField(max_length=16, null=True, blank=True)
    # TODO: Check for deprecation
    category = models.CharField(max_length=45, null=True, blank=True)
    # TODO: Check for deprecation
    code = models.CharField(max_length=10, null=True, blank=True)
    effective_datetime = models.DateTimeField(null=True, blank=True)
    # TODO: Check for deprecation
    comments = models.TextField(null=True, blank=True)
    color = models.CharField(max_length=7, null=True, blank=True)
    graph = models.TextField(default='Line')
    subject = models.ForeignKey(User, null=True, blank=True, related_name='observation_subjects', on_delete=models.DO_NOTHING)
    # TODO: Check for deprecation
    encounter = models.ForeignKey(User, null=True, blank=True, related_name='observation_encounters', on_delete=models.DO_NOTHING)
    # TODO: Check for deprecation
    performer = models.ForeignKey(User, null=True, blank=True, related_name='observation_performers', on_delete=models.DO_NOTHING)
    author = models.ForeignKey(User, null=True, blank=True, related_name='observation_authors', on_delete=models.DO_NOTHING)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_on']

    def __unicode__(self):
        return self.name


class ObservationComponent(models.Model):
    """
    Some observations have multiple component observations. These component observations are expressed as separate code
    value pairs that share the same attributes. Examples include systolic and diastolic component observations for
    blood pressure measurement and multiple component observations for genetics observations.
    """
    name = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=16, null=True, blank=True)
    component_code = models.CharField(max_length=10, null=True, blank=True)
    value_quantity = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    value_codeableconcept = models.CharField(max_length=40, null=True, blank=True)
    value_string = models.TextField(null=True, blank=True)
    value_unit = models.CharField(max_length=45, null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    effective_datetime = models.DateTimeField(null=True, blank=True)

    observation = models.ForeignKey(Observation, related_name='observation_components', on_delete=models.DO_NOTHING)
    author = models.ForeignKey(User, null=True, blank=True, related_name='observation_component_authors', on_delete=models.DO_NOTHING)

    created_on = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        ordering = ['effective_datetime', 'created_on']

    def __unicode__(self):
        return self.name


class ObservationUnit(models.Model):
    observation = models.ForeignKey(Observation, related_name='observation_units', on_delete=models.DO_NOTHING)
    value_unit = models.CharField(max_length=45, null=True, blank=True)
    is_used = models.BooleanField(default=False)


class ObservationValue(models.Model):
    status = models.CharField(max_length=16, null=True, blank=True)
    value_quantity = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    #  TODO: Refactor this field name
    value_codeableconcept = models.CharField(max_length=40, null=True, blank=True)
    value_string = models.TextField(null=True, blank=True)
    value_unit = models.CharField(max_length=45, null=True, blank=True)
    effective_datetime = models.DateTimeField(null=True, blank=True)
    component = models.ForeignKey(ObservationComponent, related_name='observation_component_values', on_delete=models.DO_NOTHING)
    author = models.ForeignKey(User, null=True, blank=True, related_name='observation_value_authors', on_delete=models.DO_NOTHING)
    created_on = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        ordering = ['effective_datetime', 'created_on']


class ObservationOrder(models.Model):
    patient = models.ForeignKey(User, null=True, blank=True, related_name="patient_observation_order", on_delete=models.DO_NOTHING)
    user = models.ForeignKey(User, null=True, blank=True, related_name="user_observation_order", on_delete=models.DO_NOTHING)
    order = ListField(null=True, blank=True)

    def __unicode__(self):
        return self.user.username


class ObservationPinToProblem(models.Model):
    author = models.ForeignKey(User, null=True, blank=True, related_name='pin_authors', on_delete=models.DO_NOTHING)
    observation = models.ForeignKey(Observation, null=True, blank=True, related_name='pin_observations', on_delete=models.DO_NOTHING)
    problem = models.ForeignKey(Problem, null=True, blank=True, related_name='pin_problems', on_delete=models.DO_NOTHING)


class Country(models.Model):
    iso3 = models.CharField(max_length=3)
    iso_num = models.CharField(max_length=3)
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return "%s" % (self.name)


class State(models.Model):
    country = models.ForeignKey(Country, related_name='country_states', on_delete=models.DO_NOTHING)
    code = models.CharField(max_length=2)
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return "%s" % (self.name)


class City(models.Model):
    state = models.ForeignKey(State, related_name='state_cities', on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return "%s" % (self.name)


class Address(models.Model):
    line1 = models.CharField(max_length=50)
    line2 = models.CharField(max_length=50)
    city = models.ForeignKey(City, related_name='city_addresses', on_delete=models.DO_NOTHING)
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
    user = models.ForeignKey(User, related_name='user_telecoms', on_delete=models.DO_NOTHING)
    telecom = models.ForeignKey(Telecom, related_name='telecom_users', on_delete=models.DO_NOTHING)
    use_code = models.CharField(max_length=6)
    rank = models.PositiveIntegerField(null=True, blank=True)
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)


class UserAddress(models.Model):
    user = models.ForeignKey(User, related_name='user_addresses', on_delete=models.DO_NOTHING)
    address = models.ForeignKey(Address, related_name='address_users', on_delete=models.DO_NOTHING)
    type_code = models.ForeignKey(AddressType, related_name='type_code_user_address', on_delete=models.DO_NOTHING)
    use_code = models.ForeignKey(AddressUse, related_name='use_code_user_address', on_delete=models.DO_NOTHING)
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)


class AOneC(models.Model):
    problem = models.OneToOneField(Problem, related_name='problem_aonecs', on_delete=models.DO_NOTHING)
    todo_past_six_months = models.BooleanField(default=False)
    patient_refused_A1C = models.BooleanField(default=False)
    observation = models.OneToOneField(Observation, related_name='observation_aonecs', on_delete=models.DO_NOTHING)

    objects = AOneCManager()


class AOneCTextNote(models.Model):
    note = models.TextField()
    a1c = models.ForeignKey(AOneC, related_name='a1c_notes', on_delete=models.DO_NOTHING)
    author = models.ForeignKey(User, null=True, blank=True, on_delete=models.DO_NOTHING)
    # TODO: Should be renamed to created_on
    datetime = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s" % (self.note)


class ObservationValueTextNote(models.Model):
    note = models.TextField()
    observation_value = models.ForeignKey(ObservationValue, related_name='observation_value_notes', on_delete=models.DO_NOTHING)
    author = models.ForeignKey(User, null=True, blank=True, on_delete=models.DO_NOTHING)

    # TODO: Should be renamed to created_on
    datetime = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s" % (self.note)


class CommonProblem(models.Model):
    """
    TODO: Should we managed two kind of problem OR one kind of problem having property to define it type
    """
    problem_name = models.CharField(max_length=200)
    concept_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    problem_type = models.CharField(max_length=10, choices=COMMON_PROBLEM_TYPE_CHOICES, default='acute')
    author = models.ForeignKey(User, null=True, blank=True, related_name="common_problem_author", on_delete=models.DO_NOTHING)


class ColonCancerScreening(models.Model):
    patient_refused = models.BooleanField(default=False)
    not_appropriate = models.BooleanField(default=False)
    risk = models.CharField(max_length=10, choices=RISK_CHOICES, default='normal')
    last_risk_updated_date = models.DateTimeField(null=True, blank=True)
    todo_past_five_years = models.BooleanField(default=False)
    patient_refused_on = models.DateTimeField(null=True, blank=True)
    not_appropriate_on = models.DateTimeField(null=True, blank=True)
    problem = models.ForeignKey(Problem, related_name='problem_colon_cancer', on_delete=models.DO_NOTHING)
    patient = models.ForeignKey(User, related_name='patient_colon_cancer', on_delete=models.DO_NOTHING)
    last_risk_updated_user = models.ForeignKey(User, related_name='last_risk_updated_user_colons', null=True,
                                               blank=True, on_delete=models.DO_NOTHING)
    created_on = models.DateTimeField(auto_now_add=True)

    objects = ColonCancerScreeningManager()

    class Meta:
        ordering = ['-created_on']


class ColonCancerStudy(models.Model):
    study_date = models.DateTimeField(null=True, blank=True)
    finding = models.CharField(max_length=100, null=True, blank=True)
    result = models.CharField(max_length=100, null=True, blank=True)
    note = models.TextField(null=True, blank=True)

    colon = models.ForeignKey(ColonCancerScreening, related_name='colon_studies', on_delete=models.DO_NOTHING)
    author = models.ForeignKey(User, related_name='author_studies', on_delete=models.DO_NOTHING)
    last_updated_user = models.ForeignKey(User, related_name='last_updated_user_studies', null=True, blank=True, on_delete=models.DO_NOTHING)

    last_updated_date = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    objects = ColonCancerStudyManager()

    class Meta:
        ordering = ['-study_date']


class ColonCancerStudyImage(models.Model):
    image = models.ImageField(upload_to='studies/', blank=True)
    author = models.ForeignKey(User, null=True, blank=True, on_delete=models.DO_NOTHING)
    study = models.ForeignKey(ColonCancerStudy, null=True, blank=True, related_name="study_images", on_delete=models.DO_NOTHING)
    datetime = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __unicode__(self):
        return self.patient

    def filename(self):
        return os.path.basename(self.image.name)


class RiskFactor(models.Model):
    colon = models.ForeignKey(ColonCancerScreening, related_name='colon_risk_factors', on_delete=models.DO_NOTHING)
    factor = models.CharField(max_length=100, null=True, blank=True)


class ColonCancerTextNote(models.Model):
    note = models.TextField()
    colon = models.ForeignKey(ColonCancerScreening, related_name='colon_notes', on_delete=models.DO_NOTHING)
    author = models.ForeignKey(User, null=True, blank=True, on_delete=models.DO_NOTHING)
    # TODO: Should be renamed to created_at
    datetime = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s" % (self.note)


class MyStoryTab(models.Model):
    name = models.TextField()
    # TODO: Why need both private & is_all. This should merged into one
    private = models.BooleanField(default=True)  # Only applied if author is Patient
    is_all = models.BooleanField(default=False)  # Only applied if author is Staff

    patient = models.ForeignKey(User, related_name="patient_story_tabs", on_delete=models.DO_NOTHING)
    author = models.ForeignKey(User, related_name="author_story_tabs", null=True,
                               blank=True, on_delete=models.DO_NOTHING)  # Patient, Patient who has accessed to the patient, Physician, Admin

    datetime = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s" % (self.name)


class MyStoryTextComponent(models.Model):
    name = models.TextField(null=True, blank=True)
    concept_id = models.CharField(max_length=20, blank=True, null=True)
    # TODO: Why need both private & is_all
    private = models.BooleanField(default=True)
    is_all = models.BooleanField(default=False)
    tab = models.ForeignKey(MyStoryTab, null=True, blank=True, related_name="my_story_tab_components", on_delete=models.DO_NOTHING)
    patient = models.ForeignKey(User, related_name="patient_story_texts", on_delete=models.DO_NOTHING)
    author = models.ForeignKey(User, related_name="author_story_texts", null=True, blank=True, on_delete=models.DO_NOTHING)
    # TODO: Should rename to created_at
    datetime = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s" % (self.name)


class MyStoryTextComponentEntry(models.Model):
    text = models.TextField(null=True, blank=True)
    component = models.ForeignKey(MyStoryTextComponent, null=True, blank=True, related_name="text_component_entries", on_delete=models.DO_NOTHING)
    patient = models.ForeignKey(User, related_name="patient_story_text_entries", null=True, blank=True, on_delete=models.DO_NOTHING)
    author = models.ForeignKey(User, related_name="author_story_text_entries", null=True, blank=True, on_delete=models.DO_NOTHING)
    datetime = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        ordering = ['-datetime']

    def __unicode__(self):
        return "%s" % self.text


class Inr(models.Model):
    """
    Medication dosage for each observation value. Can be extended later
    One data point(ObservationValue) that can be entered and viewed in more than one way.
    This is a common function for widgets and will need to be included in public API.
    """
    current_dose = models.TextField(null=True, blank=True)
    new_dosage = models.TextField(null=True, blank=True)
    next_inr = models.DateTimeField(null=True, blank=True)

    # Measured date & value is referred to observation data
    observation_value = models.OneToOneField(ObservationValue, related_name="inr", null=True, on_delete=models.DO_NOTHING)

    # Medication dosage author
    author = models.ForeignKey(User, related_name='author_inr', blank=True, null=True, on_delete=models.DO_NOTHING)
    # Can be in duplication with patient in observation value becuz this in one-2-on relationship
    patient = models.ForeignKey(User, related_name="patient_inr", null=True, on_delete=models.DO_NOTHING)

    created_on = models.DateTimeField(auto_now_add=True)  # Medication dosage created

    class Meta:
        ordering = ['-created_on']

    def __str__(self):
        return "%s" % self.observation


class InrTextNote(models.Model):
    note = models.TextField()
    author = models.ForeignKey(User, related_name="author_note", on_delete=models.DO_NOTHING)
    patient = models.ForeignKey(User, related_name="patient_note", on_delete=models.DO_NOTHING)
    # TODO: Should be rename to created_at / created_on
    datetime = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s" % (self.note)


@reversion.register()
class Medication(models.Model):
    name = models.TextField()
    concept_id = models.CharField(max_length=20, blank=True, null=True)
    current = models.BooleanField(default=True)
    # Store original medication search string for change dosage function
    search_str = models.TextField(null=True, blank=True)
    author = models.ForeignKey(User, related_name='author_medications', on_delete=models.DO_NOTHING)
    patient = models.ForeignKey(User, related_name="patient_medications", blank=True, null=True, on_delete=models.DO_NOTHING)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_on']

    def __str__(self):
        return "%s" % (self.name)


class MedicationPinToProblem(models.Model):
    author = models.ForeignKey(User, null=True, blank=True, related_name='author_pin_medications', on_delete=models.DO_NOTHING)
    medication = models.ForeignKey(Medication, related_name='medication_pin_medications', on_delete=models.DO_NOTHING)
    problem = models.ForeignKey(Problem, related_name='problem_pin_medications', on_delete=models.DO_NOTHING)


class MedicationTextNote(models.Model):
    note = models.TextField()
    medication = models.ForeignKey(Medication, related_name='medication_notes', on_delete=models.DO_NOTHING)
    author = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    datetime = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s" % (self.note)


# Merge class Document and ToDoAttachment
class Document(models.Model):
    document = models.FileField(upload_to='documents/', null=True)
    document_name = models.TextField(blank=True)
    labels = models.ManyToManyField(Label, blank=True)
    # TODO: These should being migrated to using reverse relationship
    todos = models.ManyToManyField(ToDo, blank=True, through="DocumentTodo")
    # TODO: These should being migrated to using reverse relationship
    problems = models.ManyToManyField(Problem, blank=True, through="DocumentProblem")
    # This should be always be the user who sent the request by using request object instead of pass uid directly
    author = models.ForeignKey(User, related_name='author_document', on_delete=models.DO_NOTHING)
    patient = models.ForeignKey(User, related_name='patient_pinned', null=True, blank=True, on_delete=models.DO_NOTHING)

    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_on']

    def __unicode__(self):
        return "%s" % self.document.path

    def filename(self):
        return os.path.basename(self.document.name)

    def file_extension(self):
        name, extension = os.path.splitext(self.document.name)
        extension = extension.replace('.', '')
        return extension.upper()

    def file_extension_lower(self):
        name, extension = os.path.splitext(self.document.name)
        extension = extension.replace('.', '')
        return extension

    def file_mime_type(self):
        mime = mimetypes.guess_type(self.document.path)
        return mime


class DocumentTodo(models.Model):
    document = models.ForeignKey(Document, on_delete=models.DO_NOTHING)
    todo = models.ForeignKey(ToDo, on_delete=models.DO_NOTHING)
    author = models.ForeignKey(User, on_delete=models.DO_NOTHING)  # User who attach document to the todo
    created_on = models.DateTimeField(auto_now_add=True)


class DocumentProblem(models.Model):
    document = models.ForeignKey(Document, on_delete=models.DO_NOTHING)
    problem = models.ForeignKey(Problem, on_delete=models.DO_NOTHING)
    author = models.ForeignKey(User, on_delete=models.DO_NOTHING)  # User who attach document to the problem
    created_on = models.DateTimeField(auto_now_add=True)


class GeneralSetting(models.Model):
    """
    Site settings
    setting_key is fixed & unique:
    browser_audio_recording - true/false
    todo_popup_confirm - array of affected roles
    """
    setting_key = models.TextField()
    setting_value = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)


class EncounterObservationValue(models.Model):
    encounter = models.ForeignKey(Encounter, null=False, on_delete=models.DO_NOTHING)
    observation_value = models.ForeignKey(ObservationValue, null=False, on_delete=models.DO_NOTHING)
    created_on = models.DateTimeField(auto_now_add=True)


class Narrative(models.Model):
    """

    """
    description = models.TextField()
    patient = models.ForeignKey(User, related_name="patient_narratives", on_delete=models.DO_NOTHING)
    author = models.ForeignKey(User, related_name="owned_narratives", on_delete=models.DO_NOTHING)
    parent = models.ForeignKey("Narrative", related_name="child", null=True, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(auto_now_add=True)


class VWMedications(models.Model):
    effectivetime = models.TextField()
    active = models.TextField()
    moduleid = models.TextField()
    conceptid = models.TextField()
    languagecode = models.TextField()
    typeid = models.TextField()
    term = models.TextField()
    casesignificanceid = models.TextField()

    class Meta:
        managed = False
        db_table = "vw_medications"


class VWProblems(models.Model):
    effectivetime = models.TextField()
    active = models.TextField()
    moduleid = models.TextField()
    conceptid = models.TextField()
    languagecode = models.TextField()
    typeid = models.TextField()
    term = models.TextField()
    casesignificanceid = models.TextField()

    class Meta:
        managed = False
        db_table = "vw_problems_full"


class VWTopPatients(models.Model):
    id = models.IntegerField(primary_key=True)
    username = models.TextField()
    name = models.TextField()
    user_profile_id = models.IntegerField()
    todo_count = models.IntegerField()
    problem_count = models.IntegerField()
    encounter_count = models.IntegerField()
    document_count = models.IntegerField()

    class Meta:
        managed = False
        db_table = "vw_top_patients"


class EncounterMedication(models.Model):
    encounter = models.ForeignKey(to=Encounter, related_name='medications', on_delete=models.DO_NOTHING)
    medication = models.ForeignKey(to=Medication, related_name='encounters', on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'emr_encounter_medication'
