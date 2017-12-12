from django.db import models
from django.contrib.auth.models import User
import json

class PainAvatar(models.Model):
    patient = models.ForeignKey(User)
    datetime = models.DateTimeField(auto_now_add=True)
    json = models.TextField()

    def __unicode__(self):
        return '%s %s' % (self.patient.username, self.datetime)


    def generate_dict(self):

    	obj_dict = {}
    	obj_dict['id'] = self.id

    	if self.datetime:
    		obj_dict['datetime'] = self.datetime.strftime("%Y-%m-%d %H:%M")
    	else:
    		obj_dict['datetime'] = None

    	obj_dict['json'] = json.loads(self.json)
    	return obj_dict