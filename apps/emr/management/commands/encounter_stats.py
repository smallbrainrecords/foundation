"""One-off snapshot of Encounter / EncounterEvent counts, used to compute
the smallbrain-db vs legacy delta during the 2026-06 migration."""
import json
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Count
from django.db.models.functions import TruncMonth

from emr.models import Encounter, EncounterEvent


class Command(BaseCommand):
    help = "Print Encounter/EncounterEvent stats as JSON."

    def handle(self, *args, **options):
        s = connection.settings_dict
        lat = Encounter.objects.order_by("-id").first()
        old = Encounter.objects.order_by("id").first()
        ev = EncounterEvent.objects.order_by("-id").first()

        since = datetime.now() - timedelta(days=180)
        monthly = list(
            Encounter.objects.filter(starttime__gte=since)
            .annotate(m=TruncMonth("starttime"))
            .values("m").annotate(c=Count("id")).order_by("m")
        )

        out = {
            "db_name": s.get("NAME"),
            "db_host": s.get("HOST"),
            "encounter_total": Encounter.objects.count(),
            "encounter_with_audio": Encounter.objects.exclude(audio="").count(),
            "encounter_min_id": old.id if old else None,
            "encounter_max_id": lat.id if lat else None,
            "encounter_latest_starttime": str(lat.starttime) if lat else None,
            "encounter_recent_monthly": [{"month": str(m["m"]), "count": m["c"]} for m in monthly],
            "event_total": EncounterEvent.objects.count(),
            "event_max_id": ev.id if ev else None,
        }
        self.stdout.write(json.dumps(out, indent=2, default=str))
