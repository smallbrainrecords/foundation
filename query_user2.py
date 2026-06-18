import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()
users = User.objects.filter(first_name__icontains='dunn') | User.objects.filter(last_name__icontains='dunn') | User.objects.filter(username__icontains='dunn')
for u in users:
    print(f"ID: {u.id}, Username: {u.username}, First: {u.first_name}, Last: {u.last_name}, is_active: {u.is_active}, role: {getattr(u, 'role', 'N/A')}")
