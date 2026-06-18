import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

from django.contrib.auth.models import User
from django.db.models import Count, Q

try:
    patients = User.objects.all().select_related('profile').annotate(
        problem_count_annotated=Count('problem_set', filter=Q(problem_set__is_active=True), distinct=True),
        todo_count_annotated=Count('todo_patient', filter=Q(todo_patient__accomplished=False), distinct=True)
    )
    print(list(patients)[:1])
    print("SUCCESS")
except Exception as e:
    import traceback
    traceback.print_exc()
