"""
Export recent user events to CSV, grouped by patient session.

Usage:
    python manage.py export_weekly_events
    python manage.py export_weekly_events --days 14
    python manage.py export_weekly_events --output /tmp/events.csv
"""
import csv
import json
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.analytics_app.models import UserEvent


class Command(BaseCommand):
    help = 'Export user events from the past N days to a CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days', type=int, default=7,
            help='Number of days to look back (default: 7)',
        )
        parser.add_argument(
            '--output', type=str, default=None,
            help='Output file path (default: events_export_YYYYMMDD.csv)',
        )

    def handle(self, *args, **options):
        days = options['days']
        since = timezone.now() - timedelta(days=days)

        events = (
            UserEvent.objects
            .filter(timestamp__gte=since)
            .select_related('user')
            .order_by('patient_session_id', 'sequence')
        )

        count = events.count()
        if count == 0:
            self.stdout.write(self.style.WARNING('No events found in the last %d days.' % days))
            return

        output_file = options['output'] or f"events_export_{timezone.now().strftime('%Y%m%d')}.csv"

        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp',
                'user_id',
                'username',
                'action',
                'entity_type',
                'entity_id',
                'metadata',
                'patient_session_id',
                'sequence',
                'event_schema_version',
                'app_version',
            ])

            for event in events.iterator():
                writer.writerow([
                    event.timestamp.isoformat(),
                    event.user_id,
                    event.user.username,
                    event.action,
                    event.entity_type or '',
                    event.entity_id or '',
                    json.dumps(event.metadata) if event.metadata else '',
                    event.patient_session_id,
                    event.sequence,
                    event.event_schema_version,
                    event.app_version,
                ])

        self.stdout.write(self.style.SUCCESS(
            'Exported %d events (%d days) to %s' % (count, days, output_file)
        ))
