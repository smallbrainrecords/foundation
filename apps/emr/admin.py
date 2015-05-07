from django.contrib import admin
from django.contrib.contenttypes.generic import GenericTabularInline
from models import UserProfile, AccessLog, Encounter, EncounterEvent, TextNote, Problem, Goal, ToDo, Guideline, GuidelineForm, PatientImage, Sharing, ProblemRelationship
from django.contrib.auth.models import User
admin.site.disable_action('delete_selected')
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin
from reversion.helpers import patch_admin 
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
import reversion

class EncounterEventInline(GenericTabularInline):
    model = EncounterEvent

class UserProfileAdmin(reversion.VersionAdmin):

    pass

admin.site.register(UserProfile, UserProfileAdmin)
class AccessLogAdmin(reversion.VersionAdmin):
    actions = []

admin.site.register(AccessLog, AccessLogAdmin)
from genericadmin.admin import GenericAdminModelAdmin
class EncounterAdmin(reversion.VersionAdmin, GenericAdminModelAdmin):

    inlines = [EncounterEventInline]

admin.site.register(Encounter, EncounterAdmin)

class EncounterEventAdmin(reversion.VersionAdmin, GenericAdminModelAdmin):
    pass

admin.site.register(EncounterEvent, EncounterEventAdmin)

class ProblemAdmin(reversion.VersionAdmin):
    pass

admin.site.register(Problem, ProblemAdmin)

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
admin.site.register(PatientImage, PatientImageAdmin)
admin.site.register(Sharing)
admin.site.register(ProblemRelationship)
admin.site.register(GuidelineForm)