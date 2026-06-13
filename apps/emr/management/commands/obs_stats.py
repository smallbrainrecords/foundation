"""Observation-family stats. Phase 6."""
import json
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Count
from django.db.models.functions import TruncMonth

from emr.models import Observation, ObservationComponent, ObservationValue, ObservationPinToProblem


class Command(BaseCommand):
    def handle(self, *args, **options):
        s = connection.settings_dict
        lat = Observation.objects.order_by("-id").first()
        since = datetime.now() - timedelta(days=180)
        monthly = list(
            Observation.objects.filter(created_on__gte=since)
            .annotate(m=TruncMonth("created_on"))
            .values("m").annotate(c=Count("id")).order_by("m")
        )
        val_monthly = list(
            ObservationValue.objects.filter(created_on__gte=since)
            .annotate(m=TruncMonth("created_on"))
            .values("m").annotate(c=Count("id")).order_by("m")
        )
        out = {
            "db_name": s.get("NAME"),
            "obs_total": Observation.objects.count(),
            "obs_max_id": lat.id if lat else None,
            "obs_latest_created": str(lat.created_on) if lat else None,
            "obs_monthly": [{"m": str(m["m"]), "c": m["c"]} for m in monthly],
            "obs_component_total": ObservationComponent.objects.count(),
            "obs_value_total": ObservationValue.objects.count(),
            "obs_value_monthly": [{"m": str(m["m"]), "c": m["c"]} for m in val_monthly],
            "obs_pin_total": ObservationPinToProblem.objects.count(),
        }
        self.stdout.write(json.dumps(out, indent=2, default=str))
