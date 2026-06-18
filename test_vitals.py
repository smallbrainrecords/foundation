import os
import sys

# The key is to run this using manage.py shell so the environment is fully loaded.
# I will write a simple python script that manage.py shell can execute.

script = """
from apps.emr.models import ObservationValue
from django.utils import timezone
from datetime import timedelta

recent = ObservationValue.objects.filter(created_on__gte=timezone.now() - timedelta(days=1)).order_by('-created_on')
print("Total recent vitals:", recent.count())
for v in recent[:10]:
    comp_name = v.component.name if v.component else None
    obs_name = v.observation.name if v.observation else None
    name = comp_name or obs_name
    patient = v.observation.patient.username if v.observation and v.observation.patient else "No patient"
    print(f"Vital: {name} - {v.valueQuantity} - patient: {patient} - effective: {v.effective_datetime}")
"""
with open("shell_script.py", "w") as f:
    f.write(script)
