"""`move_parked_faxes_to_office` — move faxes left in the fax review's
retired "do it later" and "set aside" states into the Office list
(2026-11-18, owner decision: the Office list replaces both).

    manage.py move_parked_faxes_to_office [--apply]

A DRY RUN unless `--apply`: it prints what it would move. Safe to run again:
a document already in Office is left as it is.

For each `DocumentReview` in `later` or `set_aside`:
  * the document gets an `OfficeDocument` row keeping who parked or set it
    aside, when, and the note (`source` is `later` or `set_aside`);
  * the review goes back to `new`, so the document starts over if it is ever
    sent back to the pool.
A set-aside document is already off every chart (set aside did that); its
`team` was restored then, which is where "back to unassigned" returns it.

Prints one JSON line of counts.
"""
import json

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from emr.models import DocumentReview, OfficeDocument


class Command(BaseCommand):
    help = "Move faxes parked in 'do it later' or set aside into the Office list (dry run unless --apply)."

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true')

    def handle(self, *args, **options):
        apply = options['apply']
        counts = {'later': 0, 'set_aside': 0, 'already_in_office': 0, 'on_a_chart': 0, 'moved': 0}
        reviews = DocumentReview.objects.filter(
            state__in=[DocumentReview.LATER, DocumentReview.SET_ASIDE]).select_related('document').order_by('id')
        for review in reviews:
            counts[review.state] += 1
            doc = review.document
            if doc.patient_id is not None:
                # Neither state leaves a document on a chart; one that is has
                # been filed since and is not ours to move.
                counts['on_a_chart'] += 1
                continue
            if OfficeDocument.objects.filter(document=doc).exists():
                counts['already_in_office'] += 1
                if apply:
                    DocumentReview.objects.filter(id=review.id).update(state=DocumentReview.NEW)
                continue
            if not apply:
                continue
            with transaction.atomic():
                locked = DocumentReview.objects.select_for_update().get(id=review.id)
                if locked.state not in (DocumentReview.LATER, DocumentReview.SET_ASIDE):
                    continue
                if locked.state == DocumentReview.LATER:
                    moved_by, moved_at, source = locked.later_by, locked.later_at, OfficeDocument.LATER
                    note = locked.note
                else:
                    moved_by, moved_at, source = locked.set_aside_by, locked.set_aside_at, OfficeDocument.SET_ASIDE
                    note = ''
                OfficeDocument.objects.get_or_create(document=doc, defaults={
                    'moved_by': moved_by, 'moved_at': moved_at or timezone.now(), 'source': source, 'note': note})
                locked.state = DocumentReview.NEW
                locked.save(update_fields=['state', 'updated_on'])
                counts['moved'] += 1
        self.stdout.write(json.dumps(dict(kind='move_parked_faxes_to_office', apply=apply, **counts)))
