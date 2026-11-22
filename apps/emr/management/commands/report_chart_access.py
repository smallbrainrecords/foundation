"""Read-only: who can open which charts, and who has been writing without that.

Run before tightening an access rule (would anyone at work be refused?) and
when reviewing accounts. Writes nothing. Prints ids, roles, dates and counts;
never a name, a username, an email or any chart text. One JSON line each.
"""
import datetime
import json
from collections import Counter, defaultdict

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.mobile_api.views import _accessible_patient_ids, _has_clinic_standing
from emr.models import (
    Encounter, MyStoryTextComponentEntry, ObservationValue, PatientController,
    PhysicianTeam,
    ProblemActivity, ProblemNote, TaggedToDoOrder, ToDo, ToDoComment,
    TodoActivity, UserProfile,
)

STAFF = ('admin', 'physician', 'mid-level', 'nurse', 'secretary')


def day(value):
    return value.date().isoformat() if value else None


class Command(BaseCommand):
    help = 'Read-only report of chart access and of writes made without it.'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=90)

    def emit(self, kind, **fields):
        fields.update(message='chart_access_report', kind=kind)
        self.stdout.write(json.dumps(fields, default=str))

    def handle(self, *args, **options):
        since = timezone.now() - datetime.timedelta(days=options['days'])
        users = {u.id: u for u in User.objects.all()}
        roles = dict(UserProfile.objects.values_list('user_id', 'role'))
        patients = {uid for uid, role in roles.items() if role == 'patient'}

        self.emit('accounts', by_role={
            '%s/%s' % (role, 'active' if active else 'inactive'): n
            for (role, active), n in Counter(
                (roles.get(u.id, 'NO PROFILE'), u.is_active) for u in users.values()).items()})

        scopes = {}

        def scope(uid):
            if uid not in scopes:
                user = users.get(uid)
                found = _accessible_patient_ids(user) if user else []
                scopes[uid] = patients if found is None else set(found)
            return scopes[uid]

        for uid, user in sorted(users.items()):
            role = roles.get(uid)
            privileged = user.is_staff or user.is_superuser
            if role != 'patient' or privileged:  # a role the rules don't know is the one to see
                self.emit(
                    'account', user_id=uid, role=role, active=user.is_active,
                    superuser=user.is_superuser, django_staff=user.is_staff,
                    joined=day(user.date_joined), last_login=day(user.last_login),
                    standing=_has_clinic_standing(user),
                    charts=len(scope(uid)))
        self.emit('patient_accounts',
                  signed_in_at_least_once=sum(1 for uid in patients if uid in users and users[uid].last_login),
                  signed_in_in_window=sum(
                      1 for uid in patients
                      if uid in users and users[uid].last_login and users[uid].last_login >= since))

        sources = [
            ('problem_activity', ProblemActivity.objects.filter(created_on__gte=since, problem__isnull=False),
             'author_id', 'problem__patient_id', 'created_on'),
            ('todo_activity', TodoActivity.objects.filter(created_on__gte=since),
             'author_id', 'todo__patient_id', 'created_on'),
            ('note', ProblemNote.objects.filter(created_on__gte=since),
             'author_id', 'problem__patient_id', 'created_on'),
            ('todo', ToDo.objects.filter(created_on__gte=since),
             'user_id', 'patient_id', 'created_on'),
            ('comment', ToDoComment.objects.filter(datetime__gte=since),
             'user_id', 'todo__patient_id', 'datetime'),
            ('reading', ObservationValue.objects.filter(created_on__gte=since),
             'author_id', 'component__observation__subject_id', 'created_on'),
            ('encounter', Encounter.objects.filter(starttime__gte=since),
             'physician_id', 'patient_id', 'starttime'),
            ('story_entry', MyStoryTextComponentEntry.objects.filter(datetime__gte=since),
             'author_id', 'patient_id', 'datetime'),
        ]
        for name, qs, who, chart, when in sources:
            total, outside, last = 0, defaultdict(set), {}
            for uid, pid, at in qs.values_list(who, chart, when).iterator():
                if uid is None or pid is None:
                    continue
                total += 1
                if pid not in scope(uid):
                    outside[uid].add(pid)
                    last[uid] = max(last.get(uid) or at, at)
            self.emit('writes', source=name, rows=total, authors_without_access=len(outside))
            for uid, charts in sorted(outside.items()):
                self.emit('write_without_access', source=name, user_id=uid, role=roles.get(uid),
                          charts=len(charts), last=day(last.get(uid)),
                          still_active=bool(users.get(uid) and users[uid].is_active))

        foreign = sum(
            1 for pid, owner, shared in MyStoryTextComponentEntry.objects.filter(
                datetime__gte=since, component__isnull=False,
            ).values_list('patient_id', 'component__patient_id', 'component__is_all')
            if pid != owner and not shared)
        self.emit('story_component_scope', entries_the_rule_would_refuse=foreign)

        hidden = Counter()
        for uid, pid in TaggedToDoOrder.objects.filter(
                todo__accomplished=False, user__is_active=True,
        ).values_list('user_id', 'todo__patient_id'):
            if roles.get(uid) != 'admin' and pid not in scope(uid):
                hidden[uid] += 1
        for uid, n in sorted(hidden.items()):
            self.emit('tags_that_would_hide', user_id=uid, role=roles.get(uid),
                      open_tags=n, last_login=day(users[uid].last_login))

        self.emit('non_staff_named', open_tags=sum(
            1 for uid, pid in TaggedToDoOrder.objects.filter(
                todo__accomplished=False, created_on__gte=since,
            ).values_list('user_id', 'todo__patient_id')
            if uid != pid and roles.get(uid) not in STAFF),
            team_rows=sum(1 for uid in PhysicianTeam.objects.values_list('member_id', flat=True)
                          if roles.get(uid) not in STAFF))

        controlled = set(PatientController.objects.values_list('patient_id', flat=True))
        self.emit('patients_without_physician', active=sum(
            1 for uid in patients
            if uid in users and users[uid].is_active and uid not in controlled))
        self.emit('done', days=options['days'])
