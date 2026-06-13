"""Stats for Problem-family tables. Used in phase-4 migration."""
import json
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Count
from django.db.models.functions import TruncMonth

from emr.models import Problem, ProblemNote, ProblemLabel, ProblemRelationship, PatientImage


class Command(BaseCommand):
    def handle(self, *args, **options):
        s = connection.settings_dict
        lat = Problem.objects.order_by("-id").first()
        old = Problem.objects.order_by("id").first()
        since = datetime.now() - timedelta(days=180)
        monthly = list(
            Problem.objects.filter(start_date__gte=since)
            .annotate(m=TruncMonth("start_date"))
            .values("m").annotate(c=Count("id")).order_by("m")
        )
        out = {
            "db_name": s.get("NAME"),
            "problem_total": Problem.objects.count(),
            "problem_min_id": old.id if old else None,
            "problem_max_id": lat.id if lat else None,
            "problem_latest_start_date": str(lat.start_date) if lat else None,
            "problem_recent_monthly": [{"m": str(m["m"]), "c": m["c"]} for m in monthly],
            "problemnote_total": ProblemNote.objects.count(),
            "problemlabel_total": ProblemLabel.objects.count(),
            "problemrelationship_total": ProblemRelationship.objects.count(),
            "patientimage_total": PatientImage.objects.count(),
        }
        self.stdout.write(json.dumps(out, indent=2, default=str))
