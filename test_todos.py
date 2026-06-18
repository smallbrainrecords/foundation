from django.utils import timezone
from emr.models import ToDo

try:
    latest_todos = ToDo.objects.all().order_by('-created_on').values('id', 'todo', 'created_on', 'problem_id')[:5]
    print("Latest 5 ToDos:")
    for t in latest_todos:
        print(f"ID: {t['id']}, Created: {t['created_on']}, Problem ID: {t['problem_id']}")
except Exception as e:
    print(f"Error querying: {e}")
