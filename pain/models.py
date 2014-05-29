from django.db import models
from django.contrib.auth.models import User

class PainAvatar(models.Model):
    patient = models.ForeignKey(User)
    datetime = models.DateTimeField(auto_now_add=True)
    json = models.TextField()

    def __unicode__(self):
        return '%s %s' % (self.patient.username, self.datetime)
