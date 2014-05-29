from django.contrib import admin
from models import PainAvatar


import reversion

class PainAvatarAdmin(reversion.VersionAdmin):

    pass

admin.site.register(PainAvatar, PainAvatarAdmin)

