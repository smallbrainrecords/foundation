"""Stats for Todo-family tables. Phase 5 of migration."""
import json
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Count
from django.db.models.functions import TruncMonth

from emr.models import ToDo, TaggedToDoOrder, ToDoComment, Label


class Command(BaseCommand):
    def handle(self, *args, **options):
        s = connection.settings_dict
        lat = ToDo.objects.order_by("-id").first()
        old = ToDo.objects.order_by("id").first()
        since = datetime.now() - timedelta(days=180)
        monthly = list(
            ToDo.objects.filter(created_on__gte=since)
            .annotate(m=TruncMonth("created_on"))
            .values("m").annotate(c=Count("id")).order_by("m")
        )
        out = {
            "db_name": s.get("NAME"),
            "todo_total": ToDo.objects.count(),
            "todo_min_id": old.id if old else None,
            "todo_max_id": lat.id if lat else None,
            "todo_latest_created_on": str(lat.created_on) if lat else None,
            "todo_recent_monthly": [{"m": str(m["m"]), "c": m["c"]} for m in monthly],
            "todocomment_total": ToDoComment.objects.count(),
            "label_total": Label.objects.count(),
            "taggedtodoorder_total": TaggedToDoOrder.objects.count(),
        }
        self.stdout.write(json.dumps(out, indent=2, default=str))
