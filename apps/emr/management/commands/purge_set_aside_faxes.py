"""`purge_set_aside_faxes` — delete documents that were set aside more than
30 days ago (emr.DocumentReview, state `set_aside`).

    manage.py purge_set_aside_faxes [--days 30] [--apply]

A set-aside fax is off every chart and out of the pool, kept so it can be
restored. RingCentral holds a received fax for about a week, so this copy is
the only one: deleting it is final. Therefore a DRY RUN unless `--apply`,
and nothing schedules it — running it, and how often, is the owner's call.

Prints one JSON line of counts. Deletes the document's file, the file as
received when pages had been removed, and the row (the review goes with it).
"""
import datetime
import json

from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.utils import timezone

from emr.models import DocumentReview


class Command(BaseCommand):
    help = "Delete faxes set aside more than --days ago (dry run unless --apply)."

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=30)
        parser.add_argument('--apply', action='store_true')

    def handle(self, *args, **options):
        days = max(30, options['days'])
        cutoff = timezone.now() - datetime.timedelta(days=days)
        reviews = DocumentReview.objects.filter(
            state=DocumentReview.SET_ASIDE, set_aside_at__lt=cutoff,
            document__patient__isnull=True).select_related('document')
        found = deleted = 0
        for review in reviews:
            found += 1
            if not options['apply']:
                continue
            doc = review.document
            names = {name for name in (doc.document.name if doc.document else '', review.original_file) if name}
            for name in names:
                try:
                    default_storage.delete(name)
                except Exception:
                    pass
            doc.delete()
            deleted += 1
        self.stdout.write(json.dumps({
            'kind': 'purge_set_aside_faxes', 'days': days, 'apply': options['apply'],
            'found': found, 'deleted': deleted}))
