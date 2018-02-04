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