"""Who may reach what (2026-11-22).

`ChartIsolationSweepTests` needs no list of endpoints: it reads every route in
`apps.mobile_api.urls`, calls each one as someone with no business on a chart,
aiming that chart's ids at it from the URL and from the body, and fails if
anything on that chart is returned or changed. A new route is covered the
moment it is mounted.
"""
import json
import re
import shutil
import tempfile
import uuid

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.test import Client, TestCase, override_settings

from emr.models import (
    CheckInDevice, CheckInSession, Document, DocumentProblem, DocumentTodo,
    Encounter, EncounterEvent, Label, MyStoryTab, MyStoryTextComponent,
    MyStoryTextComponentEntry, Observation, ObservationComponent,
    ObservationPinToProblem, ObservationValue, PatientController, PatientImage,
    PatientMutationStamp, PhysicianTeam, Problem, ProblemActivity, ProblemLabel,
    ProblemNote, ProblemRelationship, TaggedToDoOrder, ToDo, ToDoComment,
    TodoActivity, TodoProblem, UserProfile,
)
from apps.mobile_api import urls as api_urls

MARK = 'VICTIMMARK'
PW = 'invented-pass-1'
_MEDIA = tempfile.mkdtemp(prefix='access-tests-')


def tearDownModule():
    shutil.rmtree(_MEDIA, ignore_errors=True)


def api_routes():
    return [(str(p.pattern), p.callback) for p in api_urls.urlpatterns]


def fill(pattern, ids):
    path = re.sub(
        r'\(\?P<(\w+)>[^)]*\)', lambda m: str(ids.get(m.group(1), 999999)), pattern)
    path = path.lstrip('^').rstrip('$').replace('/?', '/').replace('\\', '')
    assert not re.search(r'[()\[\]*+?<>^$]', path), 'cannot fill %s' % pattern
    return '/api/' + path


def make_user(username, role, first_name=''):
    user = User.objects.create_user(
        username, '%s@example.test' % username, PW, first_name=first_name)
    if role:
        UserProfile.objects.create(user=user, role=role)
    return user


def body_of(response):
    if getattr(response, 'streaming', False):
        return b''.join(response.streaming_content)
    return response.content


class Clinic(TestCase):
    """A physician with a patient and a team; the people who are none of those."""

    def setUp(self):
        self.doctor = make_user('doctor', 'physician')
        self.team_nurse = make_user('team_nurse', 'nurse')
        self.admin = make_user('admin_user', 'admin')
        self.patient = make_user('victimmark', 'patient', MARK)
        PhysicianTeam.objects.create(physician=self.doctor, member=self.team_nurse)
        PatientController.objects.create(physician=self.doctor, patient=self.patient)

        self.outsider = make_user('outsider', 'patient')
        self.idle_nurse = make_user('idle_nurse', 'nurse')
        self.other_doctor = make_user('other_doctor', 'physician')
        self.no_profile = make_user('no_profile', None)

    def client_for(self, user=None):
        client = Client(raise_request_exception=False)
        if user is not None:
            client.force_login(user)
        return client

    def send(self, user, method, path, body=None):
        return self.client_for(user).generic(
            method, path, json.dumps(body or {}), content_type='application/json')

    def seed(self, patient, mark):
        """One of everything a chart holds."""
        by = self.doctor
        c = {}
        c['problem'] = p = Problem.objects.create(
            patient=patient, problem_name=mark + ' problem', concept_id='')
        c['problem2'] = q = Problem.objects.create(
            patient=patient, problem_name=mark + ' second', concept_id='')
        c['note'] = ProblemNote.objects.create(
            problem=p, note=mark + ' note', note_type='wiki', author=by,
            client_uuid=uuid.uuid4())
        c['problem_label'] = label = ProblemLabel.objects.create(
            name=mark + ' label', patient=patient, author=by)
        p.labels.add(label)
        c['relationship'] = ProblemRelationship.objects.create(source=p, target=q)
        c['todo'] = t = ToDo.objects.create(
            todo=mark + ' todo', patient=patient, problem=p, user=by)
        c['extra'] = TodoProblem.objects.create(todo=t, problem=q)
        c['comment'] = ToDoComment.objects.create(todo=t, user=by, comment=mark + ' comment')
        c['label'] = Label.objects.create(name=mark + ' personal', author=by, is_all=False)
        t.labels.add(c['label'])
        c['tag'] = TaggedToDoOrder.objects.create(todo=t, user=by)
        c['encounter'] = Encounter.objects.create(
            physician=by, patient=patient, transcript=mark + ' transcript',
            note=mark + ' visit', client_uuid=uuid.uuid4())
        c['encounter'].audio.save('visit.m4a', ContentFile(mark.encode()), save=True)
        c['event'] = EncounterEvent.objects.create(
            encounter=c['encounter'], summary=mark + ' event', client_uuid=uuid.uuid4())
        c['document'] = d = Document.objects.create(
            patient=patient, author=by, document_name=mark + ' document',
            extracted_text=mark + ' pages', client_uuid=uuid.uuid4())
        d.document.save('d.pdf', ContentFile(b'%PDF ' + mark.encode()), save=True)
        DocumentProblem.objects.create(document=d, problem=p, author=by)
        DocumentTodo.objects.create(document=d, todo=t, author=by)
        c['image'] = image = PatientImage(
            patient=patient, problem=p, author=by, caption=mark + ' caption',
            client_uuid=uuid.uuid4())
        image.image.save('i.jpg', ContentFile(mark.encode()), save=True)
        c['observation'] = o = Observation.objects.create(
            subject=patient, author=by, name=mark + ' vital', code='8867-4',
            client_uuid=uuid.uuid4())
        c['component'] = part = ObservationComponent.objects.create(
            observation=o, name=mark + ' part', author=by)
        c['value'] = ObservationValue.objects.create(
            component=part, value_quantity=72, author=by, client_uuid=uuid.uuid4())
        c['pin'] = ObservationPinToProblem.objects.create(
            observation=o, problem=p, author=by)
        c['tab'] = tab = MyStoryTab.objects.create(
            name=mark + ' tab', patient=patient, author=by, private=False)
        c['story'] = story = MyStoryTextComponent.objects.create(
            name=mark + ' story', tab=tab, patient=patient, author=by, private=False)
        c['entry'] = MyStoryTextComponentEntry.objects.create(
            component=story, patient=patient, author=by, text=mark + ' entry')
        c['device'] = device = CheckInDevice.objects.create(name='iPad', created_by=by)
        c['session'] = CheckInSession.objects.create(
            device=device, patient=patient, sent_by=by, form_key='check_in',
            status='submitted', client_uuid=str(uuid.uuid4()),
            answers=json.dumps({'reason': mark}))
        return c

    def url_ids(self, patient, chart, story=False):
        return {
            'patient_id': patient.id, 'user_id': patient.id,
            'problem_id': chart['problem'].id, 'note_id': chart['note'].id,
            'relationship_id': chart['relationship'].id,
            'todo_id': chart['todo'].id, 'comment_id': chart['comment'].id,
            'label_id': chart['label'].id, 'tagged_id': chart['tag'].id,
            'encounter_id': chart['encounter'].id,
            'document_id': chart['document'].id, 'image_id': chart['image'].id,
            'observation_id': chart['observation'].id,
            'component_id': (chart['story'] if story else chart['component']).id,
            'value_id': chart['value'].id, 'session_id': chart['session'].id,
            'device_id': chart['device'].id, 'team_id': self.doctor.id,
        }


@override_settings(MEDIA_ROOT=_MEDIA)
class ChartRouteAccessTests(Clinic):
    """Every route that names a chart asks whether the caller may open it."""

    # Ownership is the check: the row must be the caller's own tag.
    OWN_RULE = {'mobile_mark_tagged_todo_viewed'}

    def chart_routes(self):
        routes = [(p, cb) for p, cb in api_routes() if '(?P<patient_id>' in p]
        self.assertGreater(len(routes), 40)
        return routes

    def test_no_chart_route_answers_someone_without_the_chart(self):
        chart = self.seed(self.patient, MARK)
        for pattern, callback in self.chart_routes():
            path = fill(pattern, self.url_ids(self.patient, chart, 'my-story' in pattern))
            for user in (self.outsider, self.idle_nurse, self.other_doctor, self.no_profile):
                for method in ('GET', 'POST', 'PATCH', 'DELETE'):
                    with transaction.atomic():
                        response = self.send(user, method, path)
                        with self.subTest(route=pattern, user=user.username, method=method):
                            self.assertIn(response.status_code, (400, 403, 404, 405))
                            self.assertNotIn(MARK.encode(), body_of(response))
                        transaction.set_rollback(True)

    def test_every_gated_route_refuses_before_anything_else(self):
        gated = [(p, cb) for p, cb in self.chart_routes()
                 if getattr(cb, '_requires_patient_access', False)]
        self.assertEqual(len(gated), len({p for p, _ in gated}))
        self.assertGreaterEqual(len({cb for _, cb in gated}), 22)
        for pattern, _ in gated:
            response = self.send(
                self.outsider, 'POST', fill(pattern, {'patient_id': self.patient.id}))
            with self.subTest(route=pattern):
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response.json(), {'error': 'patient_unavailable'})

    def test_people_with_the_chart_are_never_refused_by_the_gate(self):
        for pattern, _ in self.chart_routes():
            path = fill(pattern, {'patient_id': self.patient.id})
            for user in (self.doctor, self.team_nurse, self.admin, self.patient):
                with transaction.atomic():
                    response = self.send(user, 'POST', path)
                    with self.subTest(route=pattern, user=user.username):
                        self.assertNotIn(b'patient_unavailable', body_of(response))
                    transaction.set_rollback(True)

    def test_signed_out_is_sent_to_sign_in_never_refused_as_missing(self):
        # A 404 here would make older app builds drop the edit being sent.
        for pattern, _ in self.chart_routes():
            response = self.send(None, 'POST', fill(pattern, {'patient_id': self.patient.id}))
            with self.subTest(route=pattern):
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response['Location'].startswith('/u/login/'))

    def test_a_refusal_moves_no_stamp(self):
        self.send(self.outsider, 'POST', '/api/patient/%d/problem' % self.patient.id,
                  {'problem_name': 'x'})
        self.assertFalse(PatientMutationStamp.objects.filter(patient=self.patient).exists())


class SignedOutTests(Clinic):
    """Nobody signed out gets past the door, on any route there is."""

    # Their own credential: a password, or the iPad's device token.
    OPEN = {'mobile_healthz', 'mobile_login', 'mobile_register', 'kiosk_pair', 'kiosk_current',
            'kiosk_verify', 'kiosk_photo', 'kiosk_submit', 'kiosk_abandon'}

    def test_every_other_route_sends_signed_out_to_sign_in(self):
        for pattern, callback in api_routes():
            if callback.__name__ in self.OPEN:
                continue
            for method in ('GET', 'POST', 'PATCH', 'DELETE'):
                response = self.send(None, method, fill(pattern, {}))
                with self.subTest(route=pattern, method=method):
                    self.assertEqual(response.status_code, 302)
                    self.assertTrue(response['Location'].startswith('/u/login/'))

    def test_the_open_routes_give_a_stranger_nothing(self):
        seen = set()
        for pattern, callback in api_routes():
            if callback.__name__ not in self.OPEN:
                continue
            seen.add(callback.__name__)
            if callback.__name__ == 'mobile_healthz':
                continue
            for method in ('GET', 'POST'):
                response = self.send(None, method, fill(pattern, {}))
                with self.subTest(route=pattern, method=method):
                    self.assertGreaterEqual(response.status_code, 400)
                    self.assertLess(response.status_code, 500)
        self.assertEqual(seen, self.OPEN)


@override_settings(MEDIA_ROOT=_MEDIA)
class ChartIsolationSweepTests(Clinic):
    """Every route, every method, another chart's ids in the URL and the body."""

    def setUp(self):
        super().setUp()
        self.theirs = self.seed(self.patient, MARK)
        self.pool_doc = Document.objects.create(
            team=self.doctor, author=self.doctor, document_name=MARK + ' fax',
            extracted_text=MARK + ' fax pages', client_uuid=uuid.uuid4())
        profile = self.doctor.profile
        profile.signature_image.save('sig.png', ContentFile(MARK.encode()), save=True)
        self.staff_ids = [self.doctor.id, self.team_nurse.id, self.admin.id, self.patient.id]

    def fingerprint(self):
        pid = self.patient.id
        c = self.theirs
        rows = lambda qs, *fields: sorted(repr(r) for r in qs.values_list(*fields))
        return [
            rows(User.objects.filter(id__in=self.staff_ids),
                 'id', 'email', 'first_name', 'last_name', 'password', 'is_active',
                 'is_staff', 'is_superuser'),
            rows(UserProfile.objects.filter(user_id__in=self.staff_ids),
                 'user_id', 'role', 'phone_number', 'summary', 'signature_image', 'portrait_image'),
            rows(UserProfile.objects.exclude(role='patient'), 'user_id', 'role'),
            [User.objects.count()],
            rows(PhysicianTeam.objects.all(), 'physician_id', 'member_id'),
            rows(PatientController.objects.all(), 'physician_id', 'patient_id'),
            rows(Problem.objects.filter(patient_id=pid),
                 'id', 'problem_name', 'is_active', 'is_controlled', 'authenticated', 'concept_id'),
            rows(Problem.labels.through.objects.filter(problem__patient_id=pid), 'problem_id', 'problemlabel_id'),
            rows(ProblemNote.objects.filter(id=c['note'].id), 'problem_id', 'note', 'note_type'),
            rows(ProblemNote.objects.filter(problem__patient_id=pid), 'id'),
            rows(ProblemActivity.objects.filter(problem__patient_id=pid), 'id'),
            rows(ProblemRelationship.objects.filter(source__patient_id=pid), 'source_id', 'target_id'),
            rows(ProblemRelationship.objects.filter(target__patient_id=pid), 'source_id', 'target_id'),
            rows(ToDo.objects.filter(patient_id=pid), 'id', 'todo', 'accomplished', 'problem_id', 'due_date'),
            rows(ToDo.labels.through.objects.filter(todo__patient_id=pid), 'todo_id', 'label_id'),
            rows(Label.objects.filter(id=c['label'].id), 'name', 'is_all'),
            rows(TodoActivity.objects.filter(todo__patient_id=pid), 'id'),
            rows(TodoProblem.objects.filter(todo__patient_id=pid), 'todo_id', 'problem_id'),
            rows(TodoProblem.objects.filter(problem__patient_id=pid), 'todo_id', 'problem_id'),
            rows(ToDoComment.objects.filter(todo__patient_id=pid), 'id', 'comment'),
            rows(TaggedToDoOrder.objects.filter(todo__patient_id=pid), 'user_id', 'status'),
            rows(Encounter.objects.filter(id=c['encounter'].id),
                 'patient_id', 'physician_id', 'note', 'transcript', 'audio'),
            rows(Encounter.objects.filter(patient_id=pid), 'id'),
            rows(EncounterEvent.objects.filter(id=c['event'].id), 'encounter_id', 'summary'),
            rows(EncounterEvent.objects.filter(encounter__patient_id=pid), 'id'),
            rows(Document.objects.filter(id__in=[c['document'].id, self.pool_doc.id]),
                 'id', 'patient_id', 'team_id', 'document_name', 'document', 'extracted_text', 'claimed_by_id'),
            rows(Document.objects.filter(patient_id=pid), 'id'),
            rows(DocumentProblem.objects.filter(problem__patient_id=pid), 'document_id', 'problem_id'),
            rows(DocumentTodo.objects.filter(todo__patient_id=pid), 'document_id', 'todo_id'),
            rows(PatientImage.objects.filter(id=c['image'].id), 'patient_id', 'problem_id', 'caption'),
            rows(PatientImage.objects.filter(patient_id=pid), 'id'),
            rows(Observation.objects.filter(subject_id=pid), 'id', 'comments'),
            rows(ObservationComponent.objects.filter(observation__subject_id=pid), 'id', 'name'),
            rows(ObservationValue.objects.filter(component__observation__subject_id=pid),
                 'id', 'value_quantity', 'effective_datetime'),
            rows(ObservationPinToProblem.objects.filter(problem__patient_id=pid), 'observation_id'),
            rows(ObservationPinToProblem.objects.filter(observation__subject_id=pid), 'problem_id'),
            rows(MyStoryTextComponentEntry.objects.filter(component_id=c['story'].id), 'id', 'text'),
            rows(MyStoryTextComponentEntry.objects.filter(patient_id=pid), 'id', 'text'),
            rows(CheckInSession.objects.filter(id=c['session'].id), 'status', 'applied'),
            rows(PatientMutationStamp.objects.filter(patient_id=pid), 'last_mutation_at'),
        ]

    def payload(self, n):
        c = self.theirs
        keys = [c['encounter'], c['note'], c['event'], c['document'],
                c['image'], c['value'], c['observation'], c['session']]
        targets = [self.patient, self.doctor, self.admin, self.team_nurse]
        key = str(keys[n % len(keys)].client_uuid)
        return {
            'client_uuid': key,
            'patient_id': self.patient.id, 'user_id': targets[n % len(targets)].id,
            'physician_id': self.doctor.id, 'provider_id': self.doctor.id,
            'problem_id': c['problem'].id, 'problem_ids': [c['problem'].id],
            'source_id': c['problem'].id, 'target_id': c['problem2'].id,
            'todo_id': c['todo'].id, 'todo_ids': [c['todo'].id],
            'order_todo_id': c['todo'].id,
            'document_id': c['document'].id, 'document_ids': [c['document'].id],
            'observation_value_ids': [c['value'].id], 'label_id': c['label'].id,
            'ids': [c['encounter'].id],
            'events': [{'client_uuid': str(c['event'].client_uuid), 'summary': 'changed'}],
            'matches': [{'patient_id': self.patient.id, 'strength': 'strong'}],
            'problem_name': 'changed', 'todo': 'changed', 'comment': 'changed',
            'comments': 'changed', 'note': 'changed', 'transcript': 'changed',
            'text': 'changed', 'name': 'changed', 'document_name': 'changed',
            'code': '8867-4', 'label': 'Laboratory', 'value_quantity': 99,
            'accomplished': True, 'is_active': False, 'is_controlled': True,
            'is_all': True, 'new_password': 'changed-pass-9', 'email': 'changed@example.test',
            'username': 'made%d' % n, 'password': 'changed-pass-9', 'role': 'physician',
        }

    def sweep(self, attacker):
        mine = self.seed(attacker, 'OWNDATA')
        client = self.client_for(attacker)
        before = self.fingerprint()
        changed, leaked = set(), set()
        for pattern, _ in api_routes():
            story = 'my-story' in pattern
            theirs = self.url_ids(self.patient, self.theirs, story)
            own = self.url_ids(attacker, mine, story)
            paths = [fill(pattern, theirs),
                     fill(pattern, dict(theirs, patient_id=attacker.id)),
                     fill(pattern, own),
                     fill(pattern, dict(theirs, document_id=self.pool_doc.id))]
            for path in dict.fromkeys(paths):
                shots = [('GET', None)]
                shots += [('POST', n) for n in range(8)]
                shots += [('PATCH', 0), ('DELETE', 0), ('FORM', 0), ('FORM', 2)]
                for method, n in shots:
                    broken = False
                    try:
                        with transaction.atomic():
                            if method == 'GET':
                                response = client.get(path, {'ids': str(self.theirs['encounter'].id),
                                                             'observation_id': self.theirs['observation'].id})
                            elif method == 'FORM':
                                data = {k: (json.dumps(v) if isinstance(v, list) else v)
                                        for k, v in self.payload(n).items()}
                                data['file'] = SimpleUploadedFile(
                                    'sig.png', b'%PDF changed', content_type='application/pdf')
                                response = client.post(path, data)
                            else:
                                response = client.generic(
                                    method, path, json.dumps(self.payload(n)),
                                    content_type='application/json')
                            body = body_of(response).lower()
                            broken = transaction.get_connection().needs_rollback
                            if not broken:
                                if self.fingerprint() != before:
                                    changed.add('%s %s' % (method, pattern))
                                if response.status_code < 500 and MARK.lower().encode() in body:
                                    leaked.add('%s %s' % (method, pattern))
                            transaction.set_rollback(True)
                    finally:
                        client.force_login(attacker)
        self.assertEqual(sorted(changed), [], 'changed by %s' % attacker.username)
        self.assertEqual(sorted(leaked), [], 'shown to %s' % attacker.username)

    def test_another_patient_reaches_nothing(self):
        self.sweep(self.outsider)

    def test_staff_on_no_team_reach_nothing(self):
        self.sweep(self.idle_nurse)

    def test_an_account_with_no_profile_reaches_nothing(self):
        self.sweep(self.no_profile)


@override_settings(MEDIA_ROOT=_MEDIA)
class IdempotencyKeyScopeTests(Clinic):
    """A retry key finds a row again; it never carries one to another chart."""

    def setUp(self):
        super().setUp()
        self.second = make_user('second_patient', 'patient')
        PatientController.objects.create(physician=self.doctor, patient=self.second)
        self.chart = self.seed(self.patient, MARK)
        self.problem = Problem.objects.create(
            patient=self.second, problem_name='own', concept_id='')

    def test_an_encounter_key_does_not_move_a_visit(self):
        key = str(self.chart['encounter'].client_uuid)
        response = self.send(self.doctor, 'POST', '/api/patient/%d/encounter' % self.second.id,
                             {'client_uuid': key})
        self.assertNotEqual(response.status_code, 200)
        self.chart['encounter'].refresh_from_db()
        self.assertEqual(self.chart['encounter'].patient_id, self.patient.id)

    def test_an_event_key_does_not_move_an_event(self):
        visit = Encounter.objects.create(physician=self.doctor, patient=self.second)
        response = self.send(
            self.doctor, 'PATCH', '/api/patient/%d/encounter/%d' % (self.second.id, visit.id),
            {'events': [{'client_uuid': str(self.chart['event'].client_uuid), 'summary': 'x'}]})
        self.assertLess(response.status_code, 500)
        self.chart['event'].refresh_from_db()
        self.assertEqual(self.chart['event'].encounter_id, self.chart['encounter'].id)

    def test_a_note_key_from_another_chart_is_refused(self):
        response = self.send(
            self.doctor, 'POST',
            '/api/patient/%d/problem/%d/note' % (self.second.id, self.problem.id),
            {'client_uuid': str(self.chart['note'].client_uuid), 'note': 'x'})
        self.assertEqual(response.status_code, 409)

    def test_a_shared_story_component_takes_an_entry_on_any_chart(self):
        shared = MyStoryTextComponent.objects.create(
            name='shared', patient=self.doctor, author=self.doctor, is_all=True)
        url = '/api/patient/%d/my-story/%d/entry'
        self.assertEqual(
            self.send(self.doctor, 'POST', url % (self.second.id, shared.id), {'text': 'ok'}).status_code, 200)
        self.assertEqual(
            self.send(self.doctor, 'POST', url % (self.second.id, self.chart['story'].id), {'text': 'no'}).status_code, 404)
        self.assertEqual(
            self.send(self.doctor, 'POST', url % (self.patient.id, self.chart['story'].id), {'text': 'ok'}).status_code, 200)


@override_settings(MEDIA_ROOT=_MEDIA)
class AccountRuleTests(Clinic):
    """A staff role alone does not manage other people's accounts."""

    def test_no_profile_gets_no_session(self):
        client = self.client_for()
        response = client.post('/api/login/', json.dumps({'username': 'no_profile', 'password': PW}),
                               content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertNotIn('_auth_user_id', client.session)

    def test_working_staff_still_sign_in(self):
        for user in (self.doctor, self.team_nurse, self.admin, self.idle_nurse, self.patient):
            response = self.send(None, 'POST', '/api/login/', {'username': user.username, 'password': PW})
            self.assertEqual(response.status_code, 200, user.username)

    def test_only_working_staff_create_accounts(self):
        def register(user, name):
            return self.send(user, 'POST', '/api/register/',
                             {'username': name, 'password': PW, 'role': 'nurse'}).status_code
        self.assertEqual(register(self.idle_nurse, 'new_one'), 403)
        self.assertEqual(register(self.team_nurse, 'new_two'), 200)
        self.assertEqual(register(self.doctor, 'new_three'), 200)
        self.assertEqual(register(self.admin, 'new_four'), 200)

    def test_only_working_staff_reset_a_colleague(self):
        body = {'user_id': self.doctor.id, 'new_password': 'another-pass-2'}
        self.assertEqual(self.send(self.idle_nurse, 'POST', '/api/staff-set-password/', body).status_code, 404)
        self.assertEqual(self.send(self.team_nurse, 'POST', '/api/staff-set-password/', body).status_code, 200)

    def test_active_is_staff_for_their_patient_and_admin_for_anyone(self):
        def switch(user, target):
            return self.send(user, 'POST', '/api/toggle-patient-active/',
                             {'user_id': target.id, 'is_active': True}).status_code
        self.assertEqual(switch(self.team_nurse, self.patient), 200)
        self.assertEqual(switch(self.doctor, self.patient), 200)
        self.assertEqual(switch(self.admin, self.doctor), 200)
        self.assertEqual(switch(self.team_nurse, self.admin), 404)
        self.assertEqual(switch(self.doctor, self.admin), 404)
        self.assertEqual(switch(self.idle_nurse, self.patient), 404)

    def test_a_signature_never_takes_its_key_from_the_upload(self):
        def upload(user):
            response = self.client_for(user).post(
                '/api/user/%d/signature/upload' % user.id,
                {'file': SimpleUploadedFile('signature.png', user.username.encode(), content_type='image/png')})
            self.assertEqual(response.status_code, 200)
            return UserProfile.objects.get(user=user).signature_image.name
        one, two = upload(self.doctor), upload(self.team_nurse)
        self.assertNotEqual(one, two)
        self.assertNotIn('signatures/signature.png', (one, two))

    def test_replacing_a_signature_spares_a_file_someone_else_uses(self):
        profile = self.doctor.profile
        profile.signature_image.save('legacy.png', ContentFile(b'legacy'), save=True)
        name = profile.signature_image.name
        UserProfile.objects.filter(user=self.team_nurse).update(signature_image=name)
        self.client_for(self.team_nurse).post(
            '/api/user/%d/signature/upload' % self.team_nurse.id,
            {'file': SimpleUploadedFile('signature.png', b'new', content_type='image/png')})
        self.assertTrue(profile.signature_image.storage.exists(name))  # local test storage

    def test_shared_labels_are_working_staffs_to_edit(self):
        label = Label.objects.create(name='Shared', author=self.doctor, is_all=True)
        url = '/api/labels/%d' % label.id
        self.assertEqual(self.send(self.outsider, 'PATCH', url, {'name': 'x'}).status_code, 404)
        self.assertEqual(self.send(self.team_nurse, 'PATCH', url, {'name': 'y'}).status_code, 200)

    def test_only_staff_or_the_patient_are_tagged(self):
        other = make_user('someone_else', 'patient', MARK)
        problem = Problem.objects.create(patient=self.patient, problem_name='p', concept_id='')
        todo = ToDo.objects.create(todo='t', patient=self.patient, problem=problem)
        url = '/api/patient/%d/todo/%d/member' % (self.patient.id, todo.id)
        tag = lambda target: self.send(self.team_nurse, 'POST', url, {'user_id': target.id}).status_code
        self.assertEqual([tag(self.doctor), tag(self.idle_nurse), tag(self.patient)], [200, 200, 200])
        self.assertEqual(tag(other), 404)
        self.assertFalse(TaggedToDoOrder.objects.filter(todo=todo, user=other).exists())

    def test_a_team_holds_staff_only(self):
        assign = lambda target: self.send(
            self.doctor, 'POST', '/api/team/assign/', {'user_id': target.id}).status_code
        self.assertEqual([assign(self.outsider), assign(self.no_profile)], [404, 404])
        self.assertEqual(assign(self.idle_nurse), 200)

    def test_a_requisition_names_only_staff_as_signer(self):
        other = make_user('not_a_signer', 'patient', MARK)
        problem = Problem.objects.create(patient=self.patient, problem_name='p', concept_id='')
        todo = ToDo.objects.create(todo='t', patient=self.patient, problem=problem)
        url = '/api/patient/%d/todo/%d/log-print' % (self.patient.id, todo.id)
        self.assertEqual(self.send(self.team_nurse, 'POST', url, {'provider_id': other.id}).status_code, 200)
        self.assertEqual(self.send(self.team_nurse, 'POST', url, {'provider_id': self.doctor.id}).status_code, 200)
        rows = list(TodoActivity.objects.filter(todo=todo).values_list('activity', flat=True))
        self.assertEqual(sorted(rows), ['Printed requisition', 'Printed requisition signed by doctor'])

    def test_shared_story_never_names_another_patient(self):
        first = make_user('first_owner', 'patient', MARK)
        tab = MyStoryTab.objects.create(
            name='History', patient=first, author=self.doctor, is_all=True, private=False)
        part = MyStoryTextComponent.objects.create(
            name='Surgery', tab=tab, patient=first, author=self.doctor, is_all=True, private=False)
        MyStoryTextComponentEntry.objects.create(
            component=part, patient=first, author=self.doctor, text=MARK + ' theirs')
        MyStoryTextComponentEntry.objects.create(
            component=part, patient=self.patient, author=self.doctor, text='this chart')
        response = self.send(self.doctor, 'GET', '/my_story/%d/get_my_story' % self.patient.id)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(MARK.encode(), response.content)
        self.assertIn(b'this chart', response.content)

    def test_a_tag_is_not_access_to_the_chart(self):
        problem = Problem.objects.create(patient=self.patient, problem_name='p', concept_id='')
        todo = ToDo.objects.create(todo=MARK, patient=self.patient, problem=problem)
        for user in (self.idle_nurse, self.outsider, self.team_nurse, self.admin):
            TaggedToDoOrder.objects.create(todo=todo, user=user)
        listed = lambda user: len(self.send(user, 'GET', '/api/my-tagged-todos/').json()['todos'])
        self.assertEqual([listed(self.idle_nurse), listed(self.outsider)], [0, 0])
        self.assertEqual([listed(self.team_nurse), listed(self.admin)], [1, 1])


@override_settings(MEDIA_ROOT=_MEDIA, OFFICE_ENABLED=True, OFFLINE_COPY_ENABLED=True)
class OfflineCopyIsolationTests(Clinic):
    """The offline copy's routes hand nobody another chart's files (2026-11-22).

    The sweep above catches another chart's TEXT in an answer. These routes
    answer with ids, stored file names and signed URLs, which carry none of
    it, so they are checked by key and by name: another chart's documents,
    photos and chart photo, and a pool fax of a team the caller is not on,
    never appear in a list and are never signed.
    """

    def setUp(self):
        super().setUp()
        self.theirs = self.seed(self.patient, MARK)
        UserProfile.objects.filter(user=self.patient).update(portrait_image='cover_image/victim.jpg')
        from django.utils import timezone
        PatientMutationStamp.objects.create(patient=self.patient, last_mutation_at=timezone.now())
        self.pool_doc = Document.objects.create(
            team=self.doctor, author=self.doctor, document_name='fax', client_uuid=uuid.uuid4())
        self.pool_doc.document.save('victim_fax.pdf', ContentFile(b'%PDF fax'), save=True)
        # Staff on another physician's team, with charts of their own.
        self.other_nurse = make_user('other_nurse', 'nurse')
        PhysicianTeam.objects.create(physician=self.other_doctor, member=self.other_nurse)
        self.own_patient = make_user('own_patient', 'patient')
        PatientController.objects.create(physician=self.other_doctor, patient=self.own_patient)
        self.own = self.seed(self.own_patient, 'OWNDATA')

    def their_keys(self):
        return {'document:%d' % self.theirs['document'].id,
                'image:%d' % self.theirs['image'].id,
                'portrait:%d' % self.patient.id,
                'document:%d' % self.pool_doc.id}

    def their_names(self):
        return [self.theirs['document'].document.name, self.theirs['image'].image.name,
                'cover_image/victim.jpg', self.pool_doc.document.name]

    def get(self, user, route, **query):
        return self.client_for(user).get('/api/offline/' + route, query)

    def assert_nothing_of_theirs(self, response, who):
        body = body_of(response)
        self.assertNotIn(MARK.encode(), body, who)
        for name in self.their_names():
            self.assertNotIn(name.encode(), body, '%s: %s' % (who, name))

    def test_patients_and_profileless_logins_are_refused_as_missing(self):
        keys = ','.join(sorted(self.their_keys()))
        for user in (self.outsider, self.patient, self.no_profile):
            for route in ('charts', 'files', 'file-urls'):
                response = self.get(user, route, keys=keys)
                with self.subTest(user=user.username, route=route):
                    self.assertEqual(response.status_code, 404)
                    self.assertEqual(response.json(), {'success': False, 'error': 'not_found'})
                    self.assert_nothing_of_theirs(response, user.username)

    def test_staff_without_the_chart_get_none_of_its_files(self):
        keys = ','.join(sorted(self.their_keys()))
        for user in (self.idle_nurse, self.other_doctor, self.other_nurse):
            who = user.username
            charts = self.get(user, 'charts')
            self.assertEqual(charts.status_code, 200, who)
            self.assertNotIn(self.patient.id, charts.json()['patient_ids'], who)
            self.assertNotIn(self.patient.id, [row['id'] for row in charts.json()['changed']], who)
            self.assert_nothing_of_theirs(charts, who)

            files = self.get(user, 'files')
            self.assertEqual(files.status_code, 200, who)
            listed = {f['key'] for f in files.json()['files']}
            self.assertEqual(listed & self.their_keys(), set(), who)
            self.assertNotIn(self.patient.id, files.json()['patient_ids'], who)
            self.assert_nothing_of_theirs(files, who)

            urls = self.get(user, 'file-urls', keys=keys)
            self.assertEqual(urls.status_code, 200, who)
            self.assertEqual(urls.json()['urls'], [], who)
            self.assertEqual(set(urls.json()['unavailable']), self.their_keys(), who)
            self.assert_nothing_of_theirs(urls, who)

    def test_staff_on_another_team_still_get_their_own_charts(self):
        own_document = 'document:%d' % self.own['document'].id
        for user in (self.other_doctor, self.other_nurse):
            self.assertIn(self.own_patient.id, self.get(user, 'charts').json()['patient_ids'])
            self.assertIn(own_document, {f['key'] for f in self.get(user, 'files').json()['files']})
            signed = self.get(user, 'file-urls', keys=own_document).json()
            self.assertEqual([u['key'] for u in signed['urls']], [own_document], user.username)

    def test_the_charts_own_people_get_its_files(self):
        keys = ','.join(sorted(self.their_keys()))
        for user in (self.doctor, self.team_nurse, self.admin):
            who = user.username
            self.assertIn(self.patient.id, self.get(user, 'charts').json()['patient_ids'], who)
            listed = {f['key'] for f in self.get(user, 'files').json()['files']}
            self.assertEqual(listed & self.their_keys(), self.their_keys(), who)
            signed = self.get(user, 'file-urls', keys=keys).json()
            self.assertEqual({u['key'] for u in signed['urls']}, self.their_keys(), who)
            self.assertEqual(signed['unavailable'], [], who)
