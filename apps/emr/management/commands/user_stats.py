"""User stats snapshot for the 2026-06 migration. Counts auth_user +
UserProfile + writes recent-monthly histogram."""
import json
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Count
from django.db.models.functions import TruncMonth

from emr.models import UserProfile


class Command(BaseCommand):
    help = "Print auth_user + UserProfile stats as JSON."

    def handle(self, *args, **options):
        s = connection.settings_dict
        lat = User.objects.order_by("-id").first()
        old = User.objects.order_by("id").first()

        since = datetime.now() - timedelta(days=180)
        monthly = list(
            User.objects.filter(date_joined__gte=since)
            .annotate(m=TruncMonth("date_joined"))
            .values("m").annotate(c=Count("id")).order_by("m")
        )

        out = {
            "db_name": s.get("NAME"),
            "db_host": s.get("HOST"),
            "user_total": User.objects.count(),
            "user_min_id": old.id if old else None,
            "user_max_id": lat.id if lat else None,
            "user_latest_date_joined": str(lat.date_joined) if lat else None,
            "user_recent_monthly": [{"month": str(m["m"]), "count": m["c"]} for m in monthly],
            "userprofile_total": UserProfile.objects.count(),
        }
        self.stdout.write(json.dumps(out, indent=2, default=str))
