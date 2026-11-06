"""`report_search_list_timing` — how long the chart-search list query takes on
this database for each staff login, and whether MySQL answers it from the
index meant for it.

Written 2026-11-06. The list behind `GET /api/search/charts`
(`_search_changed_at`) reads each chart's newest `extracted_text_at`. With no
index for that it read every document row, each carrying its fax text inline
after the 2026-11 text backfill, and on the db-f1-micro the clinic logins'
calls went from 8 s to past the app's 60 s timeout; chart loads stalled behind
the abandoned queries. emr 0198 added `emr_doc_patient_text_at` for it. Run
this (as a Cloud Run job) after a large text backfill, or whenever the list
seems slow, to measure the query without waiting for a Mac to ask.

Output is one JSON object per line on stdout:

  * `kind: "login"` — one per active staff login in `_SEARCH_STAFF_ROLES`:
    `user_id`, `role`, `patients` (how many charts its list covers),
    `charts_with_a_change`, `first_ms` and `second_ms` (the same query twice:
    the first may read from disk, the second mostly from memory), and on
    MySQL `document_plan_uses_index` with `document_access`, the plan steps
    that read the document table (true only when every one is a covering
    read of `emr_doc_patient_text_at`).
  * `kind: "summary"` — the slowest call and whether every plan used the
    index, last.

No names and no patient ids. Nothing is written: on MySQL the session is
READ ONLY for the duration, and the queries are the endpoint's own plus
EXPLAIN.
"""
import json
import time

from django.core.management.base import BaseCommand
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.mobile_api.views import (
    _SEARCH_STAFF_ROLES,
    _accessible_patient_ids,
    _search_changed_at,
)
from emr.models import UserProfile

INDEX_NAME = 'emr_doc_patient_text_at'


def _list_scope(user):
    """The patient ids the list endpoint asks about for `user` — the same
    substitution `mobile_search_charts` makes for an admin."""
    accessible = _accessible_patient_ids(user)
    if accessible is None:
        accessible = UserProfile.objects.filter(role='patient').values_list(
            'user_id', flat=True)
    return accessible


def _timed(patient_ids):
    started = time.perf_counter()
    changed = _search_changed_at(patient_ids)
    return round((time.perf_counter() - started) * 1000, 1), len(changed)


def _document_access(patient_ids):
    """How MySQL reads the document table for the query `_search_changed_at`
    really sends: the plan steps that read `emr_document` (`... on
    emr_document ...`), not the aggregate above them. None off MySQL."""
    if connection.vendor != 'mysql':
        return None
    with CaptureQueriesContext(connection) as queries:
        _search_changed_at(patient_ids)
    sql = [q['sql'] for q in queries.captured_queries if 'FROM `emr_document`' in q['sql']]
    if not sql:
        return None
    with connection.cursor() as cursor:
        cursor.execute('EXPLAIN FORMAT=TREE ' + sql[0])
        plan = cursor.fetchone()[0]
    lines = [line.strip().lstrip('->').strip() for line in plan.splitlines()]
    return [line for line in lines if ' on emr_document' in line]


class Command(BaseCommand):
    help = "Time the chart-search list query per staff login (read-only)."

    def handle(self, *args, **options):
        read_only = connection.vendor == 'mysql'
        if read_only:
            with connection.cursor() as cursor:
                cursor.execute('SET SESSION TRANSACTION READ ONLY')
        try:
            lines = self.report()
        finally:
            if read_only:
                with connection.cursor() as cursor:
                    cursor.execute('SET SESSION TRANSACTION READ WRITE')
        for line in lines:
            self.stdout.write(json.dumps(line))

    def report(self):
        profiles = (UserProfile.objects
                    .filter(role__in=_SEARCH_STAFF_ROLES, user__is_active=True)
                    .select_related('user')
                    .order_by('user_id'))
        lines = []
        for profile in profiles:
            # A fresh scope for every call: the endpoint passes the unevaluated
            # queryset, so its SQL carries a subquery, not a list of ids.
            patients = len(list(_list_scope(profile.user)))
            first_ms, changed = _timed(_list_scope(profile.user))
            second_ms, _ = _timed(_list_scope(profile.user))
            line = {
                'kind': 'login',
                'user_id': profile.user_id,
                'role': profile.role,
                'patients': patients,
                'charts_with_a_change': changed,
                'first_ms': first_ms,
                'second_ms': second_ms,
            }
            if patients:
                access = _document_access(_list_scope(profile.user))
                if access is not None:
                    line['document_access'] = access
                    line['document_plan_uses_index'] = bool(access) and all(
                        'Covering index' in step and INDEX_NAME in step for step in access)
            lines.append(line)

        logins = [line for line in lines if line['kind'] == 'login']
        planned = [line for line in logins if 'document_plan_uses_index' in line]
        lines.append({
            'kind': 'summary',
            'logins': len(logins),
            'slowest_first_ms': max((line['first_ms'] for line in logins), default=None),
            'slowest_second_ms': max((line['second_ms'] for line in logins), default=None),
            'plans_checked': len(planned),
            'every_plan_uses_index': all(line['document_plan_uses_index'] for line in planned)
                                     if planned else None,
        })
        return lines
