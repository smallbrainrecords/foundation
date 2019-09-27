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
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin
from django.contrib.auth.models import User
from reversion.admin import VersionAdmin

from .models import PatientController, PhysicianTeam
from .models import ProblemNote
from .models import UserProfile, Encounter, \
    EncounterEvent, TextNote, Problem, Goal, ToDo, Guideline, \
    GuidelineForm, PatientImage, Sharing, ProblemRelationship, \
    ProblemSegment, Label, ToDoAttachment, ToDoComment, LabeledToDoList, \
    Observation, \
    ObservationComponent, ObservationValue, ProblemLabel, SharingPatient, MaritalStatus, \
    CommonProblem, ColonCancerScreening, RiskFactor, ObservationPinToProblem, MyStoryTab, MyStoryTextComponent, \
    Medication, Inr, MedicationPinToProblem, MedicationTextNote, InrTextNote

# from reversion.helpers import patch_admin

admin.site.disable_action('delete_selected')


# patch_admin(User)


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


class UserProfileAdmin(VersionAdmin):
    pass


admin.site.register(UserProfile, UserProfileAdmin)


# class AccessLogAdmin(VersionAdmin):
#     actions = []


# admin.site.register(AccessLog, AccessLogAdmin)


class EncounterAdmin(VersionAdmin):
    inlines = [EncounterEventInline]


admin.site.register(Encounter, EncounterAdmin)


class EncounterEventAdmin(VersionAdmin):
    pass


admin.site.register(EncounterEvent, EncounterEventAdmin)


class ProblemAdmin(VersionAdmin):
    pass


admin.site.register(Problem, ProblemAdmin)


class ProblemSegmentAdmin(VersionAdmin):
    pass


admin.site.register(ProblemSegment, ProblemSegmentAdmin)


class GoalAdmin(VersionAdmin):
    pass


admin.site.register(Goal, GoalAdmin)


class ToDoAdmin(VersionAdmin):
    pass


admin.site.register(ToDo, ToDoAdmin)


class TextNoteAdmin(VersionAdmin):
    pass


admin.site.register(TextNote, TextNoteAdmin)


class GuidelineAdmin(VersionAdmin):
    pass


admin.site.register(Guideline, GuidelineAdmin)


class PatientImageAdmin(VersionAdmin):
    pass


class PatientControllerAdmin(VersionAdmin):
    list_display = ['patient', 'physician']


class ObservationComponentAdmin(VersionAdmin):
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
admin.site.register(InrTextNote)

# TODO: AnhDN(1/12/2017) Need to understand why need to patch_admin to able to view reversion from other app
# patch_admin(Medication)
