"""The full copy of the practice each clinic Mac keeps for an internet
outage, and for opening charts instantly (2026-11-22; app plan:
SBR1 PLAN_OFFLINE_FULL_COPY_2026-11.md).

Owner decisions, 2026-11-21/22:

  * Every ACTIVE chart the login may see, pulled once overnight and then kept
    current. Inactive patients are not part of the copy.
  * Every chart PDF filed in the past 12 months, every fax waiting in the
    unassigned list and every Office document.
  * Photos added to problems, and patients' chart photos.
  * Visit audio is not part of it.

Three routes, all read-only and staff-only:

  * `offline/charts` says which charts are in the copy and which changed. The
    Mac then pulls those charts through the ordinary `patient_full`; nothing
    here reads a chart.
  * `offline/files` lists the files in the copy.
  * `offline/file-urls` signs short-lived storage URLs for a batch of them,
    so the bytes never pass through Cloud Run (its 32 MiB response cap, and
    four request slots an instance).

**A refusal is a JSON 404, never a 403**: the app reads 403 as signed out. A
404 without a JSON body is a server without these routes.

**Every Mac asks these every few minutes, so none may read a row it does not
need.** On 2026-11-06 a list query that read every document row (fax text
inline) held the service's request slots for minutes. The chart list reads
ids, the stamp table's index and the encounter table's patient index; the
chart-file half of the file list is answered by `emr_doc_created_file_idx`
alone (`OfflineCopyQueryPlanTests`).

**A file storage does not have is left out of the list** (2026-11-24). The
list never asks storage, so a record whose file is gone was listed for good,
and every Mac that listed it said "Not complete" for good (17 legacy photos
on the first real fill). `check_offline_files` asks storage once and records
those files in `MissingStoredFile`; `_without_missing` drops them, matched on
the stored name too, so a record that gets a new file is listed again.

`OFFLINE_COPY_ENABLED=false` switches it off: every route answers
`enabled: false` and each Mac returns to loading charts as they are opened.
"""
import datetime
import re

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Max
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.gzip import gzip_page

from emr.models import (
    Document, Encounter, MissingStoredFile, OfficeDocument, PatientImage, PatientMutationStamp,
    UserProfile,
)

from . import views as api

#: Files one `file-urls` request may ask for. Each URL is one SignBlob call,
#: so this bounds how long the request holds its slot.
MAX_URLS_PER_REQUEST = 20

_KEY_RE = re.compile(r'^(document|image|portrait):([0-9]{1,18})$')


def enabled():
    return bool(getattr(settings, 'OFFLINE_COPY_ENABLED', True))


def _not_found():
    return JsonResponse({'success': False, 'error': 'not_found'}, status=404)


def _gate(request):
    """The checks every route shares. A response to send, or None."""
    if api._role_of(request.user) not in api._SEARCH_STAFF_ROLES:
        return _not_found()
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'GET required'}, status=405)
    if not enabled():
        return JsonResponse({'success': True, 'enabled': False})
    return None


def active_patient_ids(user, among=None):
    """The patients whose charts are in `user`'s copy: active accounts among
    the charts they may open (`_accessible_patient_ids`). `among` narrows the
    answer to those ids."""
    patients = User.objects.filter(is_active=True, profile__role='patient')
    accessible = api._accessible_patient_ids(user)
    if accessible is not None:
        patients = patients.filter(id__in=accessible)
    if among is not None:
        patients = patients.filter(id__in=list(among))
    return set(patients.order_by().values_list('id', flat=True))


def files_since(now):
    """The start of the 12-month window: the same day a year before."""
    try:
        return now.replace(year=now.year - 1)
    except ValueError:  # 29 February
        return now.replace(year=now.year - 1, day=28)


def _parse_since(raw):
    """(since, ok). An unencoded '+' arrives as a space, as on `/changed`."""
    if not raw:
        return None, True
    try:
        since = parse_datetime(raw)
        if since is None and ' ' in raw and 'T' in raw:
            since = parse_datetime(raw.replace(' ', '+'))
    except ValueError:  # well formed, not a real date
        return None, False
    if since is None:
        return None, False
    if timezone.is_naive(since):
        since = timezone.make_aware(since, datetime.timezone.utc)
    return since, True


def _most_recent_first(patient_ids, stamps, latest_visit):
    """Order for a Mac's first fill, so half a night still covers the likely
    patients: a chart ranks by the better of "changed lately" and "seen
    lately". The stamp alone would let a bulk repair job outrank visits, and
    it is empty for a chart untouched since stamps began."""
    ids = sorted(patient_ids)
    never = len(ids)
    by_change = sorted((p for p in ids if p in stamps), key=lambda p: stamps[p], reverse=True)
    by_visit = sorted((p for p in ids if p in latest_visit), key=lambda p: latest_visit[p], reverse=True)
    change_rank = {p: rank for rank, p in enumerate(by_change)}
    visit_rank = {p: rank for rank, p in enumerate(by_visit)}

    def rank(patient_id):
        first = change_rank.get(patient_id, never)
        second = visit_rank.get(patient_id, never)
        return (min(first, second), second, first, -patient_id)

    return sorted(ids, key=rank)


@csrf_exempt
@login_required
@gzip_page
def mobile_offline_charts(request):
    """GET [?since=<ISO 8601>] -> the charts in this login's copy.

    `{success, enabled, server_time, full, patient_ids, changed: [{id,
    changed_at}]}`.

    `patient_ids` is always every chart in the copy, so a patient made active
    or inactive, or access gained or lost, shows at the next ask without a
    stamp. Without `since` it is most recently active first and `changed`
    holds every chart's stamp; with `since`, only stamps moved after it.

    `changed_at` is `PatientMutationStamp.last_mutation_at`, written the same
    way `patient_full` writes `chart_changed_at`: the app compares the two
    strings for equality, so a stamp that commits after a chart was read is
    still noticed. `server_time` is captured before every read.
    """
    refusal = _gate(request)
    if refusal:
        return refusal
    since, ok = _parse_since(request.GET.get('since'))
    if not ok:
        return JsonResponse({'success': False, 'error': 'invalid_since'}, status=400)

    server_time = timezone.now()
    patients = active_patient_ids(request.user)

    moved = PatientMutationStamp.objects.all()
    if since is not None:
        moved = moved.filter(last_mutation_at__gt=since)
    stamps = {
        patient_id: at
        for patient_id, at in moved.order_by().values_list('patient_id', 'last_mutation_at')
        if patient_id in patients
    }

    if since is None:
        # The highest encounter id per patient stands for the latest visit:
        # it comes from the patient index alone, where MAX(starttime) would
        # read every visit's row, transcript and all.
        latest_visit = {
            row['patient_id']: row['latest']
            for row in Encounter.objects.order_by().values('patient_id').annotate(latest=Max('id'))
            if row['patient_id'] in patients
        }
        ordered = _most_recent_first(patients, stamps, latest_visit)
    else:
        ordered = sorted(patients)

    return JsonResponse({
        'success': True,
        'enabled': True,
        'server_time': api._iso_z(server_time),
        'full': since is None,
        'patient_ids': ordered,
        'changed': [{'id': p, 'changed_at': api._iso_z(stamps[p])} for p in sorted(stamps)],
    })


def _file_json(key, kind, record_id, file_path, patient_id=None, team_id=None,
               file_size=None, created_on=None, version=None):
    return {
        'key': key,
        'kind': kind,
        'id': record_id,
        'patient_id': patient_id,
        'team_id': team_id,
        'file_path': file_path,
        'file_size': file_size,
        'created_on': api._iso_z(created_on) if created_on else None,
        'version': version,
    }


def _chart_document_rows(since):
    """Every document filed since `since`, from the index alone. The patient
    test happens in Python: an IN list of 1,500 patients would turn this
    range into a lookup of each patient's whole history."""
    return Document.objects.filter(created_on__gte=since).order_by().values_list(
        'id', 'patient_id', 'document', 'file_size', 'created_on')


def _chart_files(patients, since):
    return [
        _file_json('document:%d' % doc_id, 'chart', doc_id, path,
                   patient_id=patient_id, file_size=size, created_on=created)
        for doc_id, patient_id, path, size, created in _chart_document_rows(since)
        if path and patient_id in patients
    ]


def _pool_files(team_ids):
    """The unassigned list's own rule (`mobile_unassigned_documents_list`)."""
    if team_ids is not None and not team_ids:
        return []
    waiting = Document.objects.filter(patient__isnull=True, team__isnull=False).exclude(
        office__isnull=False).exclude(review__state='set_aside')
    if team_ids is not None:
        waiting = waiting.filter(team_id__in=team_ids)
    return [
        _file_json('document:%d' % doc_id, 'pool', doc_id, path,
                   team_id=team_id, file_size=size, created_on=created)
        for doc_id, team_id, path, size, created in waiting.order_by().values_list(
            'id', 'team_id', 'document', 'file_size', 'created_on')
        if path
    ]


def _office_files():
    if not getattr(settings, 'OFFICE_ENABLED', True):
        return []
    in_office = OfficeDocument.objects.order_by().values_list(
        'document_id', 'document__team_id', 'document__document',
        'document__file_size', 'document__created_on')
    return [
        _file_json('document:%d' % doc_id, 'office', doc_id, path,
                   team_id=team_id, file_size=size, created_on=created)
        for doc_id, team_id, path, size, created in in_office
        if path
    ]


def _image_files(patients):
    """Photos on problems, of any age: `patient_full` sends every one."""
    images = PatientImage.objects.filter(problem__isnull=False).order_by().values_list(
        'id', 'problem__patient_id', 'image', 'datetime')
    return [
        _file_json('image:%d' % image_id, 'image', image_id, path,
                   patient_id=patient_id, created_on=created)
        for image_id, patient_id, path, created in images
        if path and patient_id in patients
    ]


def _portrait_files(patients):
    profiles = UserProfile.objects.filter(role='patient').exclude(
        portrait_image='').order_by().values_list('user_id', 'portrait_image')
    found = []
    for user_id, path in profiles:
        version = api.portrait_version_for_name(path)
        if version and user_id in patients:
            found.append(_file_json('portrait:%d' % user_id, 'portrait', user_id, path,
                                    patient_id=user_id, version=version))
    return found


def _without_missing(files):
    """`files` without those storage was found not to have
    (`check_offline_files`): no Mac can ever copy them, and each that lists
    one says "Not complete" for good. Matched on the stored name as well as
    the key, so a record that gets a new file is listed again."""
    missing = dict(MissingStoredFile.objects.values_list('key', 'file_path'))
    if not missing:
        return files
    return [f for f in files if missing.get(f['key']) != f['file_path']]


@csrf_exempt
@login_required
@gzip_page
def mobile_offline_files(request):
    """GET -> every file in this login's copy.

    `{success, enabled, server_time, since, patient_ids, team_ids, files}`.

    `file_path` is the stored name; a new version of a document has a new
    one, which is how a Mac knows its copy is old. `patient_ids` and
    `team_ids` (null: every team) say what the list covers, so a Mac deletes
    a cached file only when this list really would have named it. A file
    storage is known not to have is left out (`_without_missing`).
    """
    refusal = _gate(request)
    if refusal:
        return refusal

    server_time = timezone.now()
    since = files_since(server_time)
    patients = active_patient_ids(request.user)
    team_ids = api._user_team_ids(request.user)

    files = _without_missing(
        _chart_files(patients, since) + _pool_files(team_ids) + _office_files()
        + _image_files(patients) + _portrait_files(patients))
    # Newest first: the order a Mac downloads in.
    files.sort(key=lambda f: (f['created_on'] or '', f['key']), reverse=True)

    return JsonResponse({
        'success': True,
        'enabled': True,
        'server_time': api._iso_z(server_time),
        'since': api._iso_z(since),
        'patient_ids': sorted(patients),
        'team_ids': None if team_ids is None else sorted(team_ids),
        'files': files,
    })


def _readable_files(user, keys):
    """{key: (storage, stored name)} for the keys `user` may read, by the
    rules the file list is built with."""
    wanted = {'document': [], 'image': [], 'portrait': []}
    for kind, record_id in keys:
        wanted[kind].append(record_id)

    documents, images, portraits = [], [], []
    if wanted['document']:
        documents = list(Document.objects.filter(id__in=wanted['document']).order_by().values_list(
            'id', 'patient_id', 'team_id', 'document'))
    if wanted['image']:
        images = list(PatientImage.objects.filter(
            id__in=wanted['image'], problem__isnull=False,
        ).order_by().values_list('id', 'problem__patient_id', 'image'))
    if wanted['portrait']:
        portraits = list(UserProfile.objects.filter(
            user_id__in=wanted['portrait'], role='patient',
        ).order_by().values_list('user_id', 'portrait_image'))

    asked_patients = (
        {p for _, p, _, _ in documents if p is not None}
        | {p for _, p, _ in images if p is not None}
        | {p for p, _ in portraits}
    )
    patients = active_patient_ids(user, among=asked_patients) if asked_patients else set()

    unfiled = [doc_id for doc_id, patient_id, _, _ in documents if patient_id is None]
    in_office = set()
    team_ids = set()
    if unfiled:
        in_office = set(OfficeDocument.objects.filter(
            document_id__in=unfiled).values_list('document_id', flat=True))
        team_ids = api._user_team_ids(user)

    storage_of = {
        'document': Document._meta.get_field('document').storage,
        'image': PatientImage._meta.get_field('image').storage,
        'portrait': UserProfile._meta.get_field('portrait_image').storage,
    }
    readable = {}
    for doc_id, patient_id, team_id, path in documents:
        if not path:
            continue
        if patient_id is not None:
            allowed = patient_id in patients
        elif doc_id in in_office:
            allowed = bool(getattr(settings, 'OFFICE_ENABLED', True))
        else:
            allowed = team_id is not None and (team_ids is None or team_id in team_ids)
        if allowed:
            readable['document:%d' % doc_id] = (storage_of['document'], path)
    for image_id, patient_id, path in images:
        if path and patient_id in patients:
            readable['image:%d' % image_id] = (storage_of['image'], path)
    for user_id, path in portraits:
        if user_id in patients and api.portrait_version_for_name(path):
            readable['portrait:%d' % user_id] = (storage_of['portrait'], path)
    return readable


@csrf_exempt
@login_required
def mobile_offline_file_urls(request):
    """GET ?keys=document:1,image:2,portrait:3 -> short-lived URLs.

    `{success, enabled, expires_in, urls: [{key, file_path, url}],
    unavailable: [keys]}`. At most `MAX_URLS_PER_REQUEST` keys.

    `unavailable` is a key this login may not read, or one that is gone; the
    two are not told apart. `url` is null when signing failed. The server
    does NOT fall back to relaying the bytes, as `mobile_encounter_audio`
    does: thousands of files through four request slots is the load this
    route exists to avoid. The Mac asks again later.
    """
    refusal = _gate(request)
    if refusal:
        return refusal

    keys = []
    for raw in (request.GET.get('keys') or '').split(','):
        raw = raw.strip()
        if not raw:
            continue
        match = _KEY_RE.match(raw)
        if not match:
            return JsonResponse({'success': False, 'error': 'invalid_keys'}, status=400)
        parsed = (match.group(1), int(match.group(2)))
        if parsed not in keys:
            keys.append(parsed)
    if not keys or len(keys) > MAX_URLS_PER_REQUEST:
        return JsonResponse({'success': False, 'error': 'invalid_keys'}, status=400)

    readable = _readable_files(request.user, keys)
    sign = api._media_url_signer()
    urls, unavailable = [], []
    for kind, record_id in keys:
        key = '%s:%d' % (kind, record_id)
        if key not in readable:
            unavailable.append(key)
            continue
        storage, name = readable[key]
        urls.append({'key': key, 'file_path': name, 'url': sign(storage, name)})

    return JsonResponse({
        'success': True,
        'enabled': True,
        'expires_in': int(api._SIGNED_URL_TTL.total_seconds()),
        'urls': urls,
        'unavailable': unavailable,
    })
