"""Document-family stats. Phase 8."""
import json
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Count
from django.db.models.functions import TruncMonth

from emr.models import Document, DocumentTodo, DocumentProblem


class Command(BaseCommand):
    def handle(self, *args, **options):
        s = connection.settings_dict
        lat = Document.objects.order_by("-id").first()
        since = datetime.now() - timedelta(days=180)
        monthly = list(
            Document.objects.filter(created_on__gte=since)
            .annotate(m=TruncMonth("created_on"))
            .values("m").annotate(c=Count("id")).order_by("m")
        )
        out = {
            "db_name": s.get("NAME"),
            "doc_total": Document.objects.count(),
            "doc_max_id": lat.id if lat else None,
            "doc_latest_created": str(lat.created_on) if lat else None,
            "doc_monthly": [{"m": str(m["m"]), "c": m["c"]} for m in monthly],
            "docproblem_total": DocumentProblem.objects.count(),
            "doctodo_total": DocumentTodo.objects.count(),
        }
        self.stdout.write(json.dumps(out, indent=2, default=str))
