"""Find the files the offline copy would list that storage does not have
(2026-11-24).

The offline copy's file list is built from the database alone; nothing asks
storage while a list is built. A record whose file is gone can therefore
never be copied, and every Mac that lists it says "Not complete" for good.
The first real fill (2026-11-23) met 17: eight problem photos from 2022 and
nine chart photos, every one a 404 in the bucket.

This asks storage once for every file any login's list could offer (chart
PDFs of the past year on active charts, pool and Office documents, problem
photos and chart photos) and keeps `MissingStoredFile` in step: a row for
each file storage doesn't have, and none for one it has again. The list
leaves those files out (`offline_copy._without_missing`). A file not offered
this run (an inactive chart, a document past the year) keeps its row: it
wasn't asked about.

Dry run unless --apply. One JSON line out: how many files of each kind were
checked, the keys found missing (record ids only: a stored name can carry a
patient's name), and what --apply adds and removes.

Only "not there" counts as missing. Any other storage error stops the run
before anything is written: a file must never be left out of every Mac's
copy because storage was briefly unreachable.

Run it again after a bulk import or a storage restore; nothing else should
add a missing file (an upload stores the file before the record).
"""
import collections
import json

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.mobile_api import offline_copy
from emr.models import Document, MissingStoredFile, PatientImage, UserProfile
from emr.storable import stored_file_exists


def offered_files(now):
    """{key: (kind, stored name)} for every file some login's list could
    offer: the list's own rules, over every active chart and every team."""
    patients = set(User.objects.filter(is_active=True, profile__role='patient')
                   .order_by().values_list('id', flat=True))
    since = offline_copy.files_since(now)
    listed = (offline_copy._chart_files(patients, since) + offline_copy._pool_files(None)
              + offline_copy._office_files() + offline_copy._image_files(patients)
              + offline_copy._portrait_files(patients))
    offered = {}
    for file in listed:
        offered.setdefault(file['key'], (file['kind'], file['file_path']))
    return offered


class Command(BaseCommand):
    help = ("Record the files the offline copy would list that storage does not have, "
            "so the list leaves them out. Dry run unless --apply.")

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true',
                            help='Write the result to MissingStoredFile.')

    def handle(self, *args, **options):
        apply = options['apply']
        now = timezone.now()
        storage_of = {
            'document': Document._meta.get_field('document').storage,
            'image': PatientImage._meta.get_field('image').storage,
            'portrait': UserProfile._meta.get_field('portrait_image').storage,
        }

        checked = collections.Counter()
        missing, present = {}, set()
        # Every check before any write: a storage error raises out of here.
        for key, (kind, name) in offered_files(now).items():
            checked[kind] += 1
            if stored_file_exists(name, storage_of[key.split(':', 1)[0]]):
                present.add(key)
            else:
                missing[key] = name

        recorded = dict(MissingStoredFile.objects.values_list('key', 'file_path'))
        add = sorted(key for key, name in missing.items() if recorded.get(key) != name)
        remove = sorted(key for key in recorded if key in present)
        if apply:
            with transaction.atomic():
                if remove:
                    MissingStoredFile.objects.filter(key__in=remove).delete()
                for key in add:
                    MissingStoredFile.objects.update_or_create(
                        key=key, defaults={'file_path': missing[key], 'checked_on': now})
                still = [key for key in missing if key not in add]
                if still:
                    MissingStoredFile.objects.filter(key__in=still).update(checked_on=now)

        self.stdout.write(json.dumps({
            'event': 'check_offline_files',
            'applied': apply,
            'checked': dict(checked),
            'checked_total': sum(checked.values()),
            'missing': sorted(missing),
            'missing_total': len(missing),
            'added' if apply else 'would_add': add,
            'removed' if apply else 'would_remove': remove,
        }, sort_keys=True))
