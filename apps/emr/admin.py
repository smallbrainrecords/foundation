from django.contrib import admin

from .models import UserProfile, AccessLog, Encounter, \
    EncounterEvent, TextNote, Problem, Goal, ToDo, Guideline,\
    GuidelineForm, PatientImage, Sharing, ProblemRelationship, \
    ProblemSegment

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


class ToDoInline(admin.StackedInline):
    model = ToDo
    extra = 0


class UserAdmin(AuthUserAdmin):
    inlines = [UserProfileInline, ProblemInline, GoalInline, ToDoInline]

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


admin.site.register(PatientImage, PatientImageAdmin)
admin.site.register(Sharing)
admin.site.register(ProblemRelationship)
admin.site.register(GuidelineForm)
admin.site.register(PatientController, PatientControllerAdmin)
admin.site.register(PhysicianTeam)
admin.site.register(ProblemNote)
