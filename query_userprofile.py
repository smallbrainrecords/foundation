import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

from emr.models import UserProfile
users = UserProfile.objects.filter(first_name__icontains='keegan') | UserProfile.objects.filter(last_name__icontains='keegan') | UserProfile.objects.filter(first_name__icontains='dunn') | UserProfile.objects.filter(last_name__icontains='dunn')
for u in users:
    print(f"ID: {u.id}, First: {u.first_name}, Last: {u.last_name}, Role: {u.role}")
