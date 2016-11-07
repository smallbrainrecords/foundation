from django.contrib import admin

from .models import UserProfile, AccessLog, Encounter, \
    EncounterEvent, TextNote, Problem, Goal, ToDo, Guideline,\
    GuidelineForm, PatientImage, Sharing, ProblemRelationship, \
    ProblemSegment, Label, ToDoAttachment, ToDoComment, LabeledToDoList, \
    Country, State, City, TelecomSystem, Telecom, AddressType, AddressUse, Observation, \
    ObservationComponent, ObservationValue, ProblemLabel, SharingPatient, MaritalStatus, \
    CommonProblem, ColonCancerScreening, RiskFactor, ObservationPinToProblem, MyStoryTab, MyStoryTextComponent, \
    Medication, Inr, MedicationPinToProblem, MedicationTextNote, InrValue

from .models import PatientController, PhysicianTeam
from .models import ProblemNote
from django.contrib.auth.models import User


from django.contrib.auth.admin import UserAdmin as AuthUserAdmin
from reversion.helpers import patch_admin

import reversion

admin.site.disable_action('delete_selected')
patch_admin(User)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    max_num = 1
    can_delete = False


class ProblemInline(admin.StackedInline):
    model = Problem
    extra = 0


class GoalInline(admin.StackedInline):
    model = Goal
    extra = 0


class UserAdmin(AuthUserAdmin):
    inlines = [UserProfileInline, ProblemInline, GoalInline]

# unregister old user admin
admin.site.unregister(User)
# register new user admin
admin.site.register(User, UserAdmin)


class EncounterEventInline(admin.StackedInline):
    model = EncounterEvent


class UserProfileAdmin(reversion.VersionAdmin):
    pass

admin.site.register(UserProfile, UserProfileAdmin)


class AccessLogAdmin(reversion.VersionAdmin):
    actions = []

admin.site.register(AccessLog, AccessLogAdmin)


class EncounterAdmin(reversion.VersionAdmin):

    inlines = [EncounterEventInline]

admin.site.register(Encounter, EncounterAdmin)


class EncounterEventAdmin(reversion.VersionAdmin):
    pass

admin.site.register(EncounterEvent, EncounterEventAdmin)


class ProblemAdmin(reversion.VersionAdmin):
    pass

admin.site.register(Problem, ProblemAdmin)


class ProblemSegmentAdmin(reversion.VersionAdmin):
    pass

admin.site.register(ProblemSegment, ProblemSegmentAdmin)


class GoalAdmin(reversion.VersionAdmin):
    pass

admin.site.register(Goal, GoalAdmin)


class ToDoAdmin(reversion.VersionAdmin):
    pass

admin.site.register(ToDo, ToDoAdmin)


class TextNoteAdmin(reversion.VersionAdmin):
    pass


admin.site.register(TextNote, TextNoteAdmin)


class GuidelineAdmin(reversion.VersionAdmin):
    pass
admin.site.register(Guideline, GuidelineAdmin)


class PatientImageAdmin(reversion.VersionAdmin):
    pass


class PatientControllerAdmin(reversion.VersionAdmin):
    list_display = ['patient', 'physician']


class ObservationComponentAdmin(reversion.VersionAdmin):
    list_display = ['name', 'get_observation_name', 'get_observation_id']

    def get_observation_name(self, obj):
        return obj.observation.name
    get_observation_name.short_description = 'Observation name'
    get_observation_name.admin_order_field = 'observation__name'

    def get_observation_id(self, obj):
        return obj.observation.id
    get_observation_id.short_description = 'Observation id'
    get_observation_id.admin_order_field = 'observation__id'


admin.site.register(PatientImage, PatientImageAdmin)
admin.site.register(Sharing)
admin.site.register(ProblemRelationship)
admin.site.register(GuidelineForm)
admin.site.register(PatientController, PatientControllerAdmin)
admin.site.register(PhysicianTeam)
admin.site.register(ProblemNote)
admin.site.register(Label)
admin.site.register(ToDoAttachment)
admin.site.register(ToDoComment)
admin.site.register(LabeledToDoList)
admin.site.register(Observation)
admin.site.register(ObservationComponent, ObservationComponentAdmin)
admin.site.register(ObservationValue)
admin.site.register(ProblemLabel)
admin.site.register(SharingPatient)
admin.site.register(MaritalStatus)
admin.site.register(CommonProblem)
admin.site.register(ColonCancerScreening)
admin.site.register(RiskFactor)
admin.site.register(ObservationPinToProblem)
admin.site.register(MyStoryTab)
admin.site.register(MyStoryTextComponent)
admin.site.register(Medication)
admin.site.register(Inr)
admin.site.register(MedicationPinToProblem)
admin.site.register(MedicationTextNote)
admin.site.register(InrValue)