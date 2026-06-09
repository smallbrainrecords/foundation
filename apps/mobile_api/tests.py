"""
Tests for the mobile_api PATCH endpoints that flow through the iOS
bidirectional sync pipeline. Currently covers mobile_update_encounter:
this endpoint is the source-of-truth gate for Encounter updates that
post-date the initial audio-upload POST (notably transcript and
post-stop note/recorder_status changes).
"""
import json

from django.test import TestCase, Client
from django.contrib.auth.models import User

from django.core.files.uploadedfile import SimpleUploadedFile

from emr.models import (
    Encounter, EncounterEvent,
    EncounterProblemRecord, EncounterTodoRecord, EncounterObservationValue,
    Problem, ProblemNote, ProblemActivity,
    ToDo, Observation, ObservationComponent, ObservationValue,
    ObservationPinToProblem,
    UserProfile, PatientController, PhysicianTeam,
    PatientImage, Document, DocumentProblem, DocumentTodo,
)


class MobileUpdateEncounterTests(TestCase):
    def setUp(self):
        self.physician = User.objects.create_user(
            username='doc_a', password='top_secret',
            email='doc_a@example.com',
        )
        self.patient = User.objects.create_user(
            username='pt_a', password='unused',
            email='pt_a@example.com',
        )
        self.other_patient = User.objects.create_user(
            username='pt_b', password='unused',
            email='pt_b@example.com',
        )

        self.encounter = Encounter.objects.create(
            physician=self.physician,
            patient=self.patient,
            note='initial',
            recorder_status=0,
        )

        self.client = Client()
        self.client.login(username='doc_a', password='top_secret')

    # ---- success path ----

    def test_patch_updates_transcript_and_note(self):
        url = f'/api/patient/{self.patient.id}/encounter/{self.encounter.id}'
        body = {
            'note': 'updated note',
            'transcript': 'patient reports feeling better',
            'recorder_status': 2,
        }
        resp = self.client.patch(url, data=json.dumps(body), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertTrue(data['success'])
        # Response now also carries the events sync_id → server_id map; with no
        # events sent it's an empty list.
        self.assertEqual(data.get('events'), [])

        self.encounter.refresh_from_db()
        self.assertEqual(self.encounter.note, 'updated note')
        self.assertEqual(self.encounter.transcript, 'patient reports feeling better')
        self.assertEqual(self.encounter.recorder_status, 2)

    # ---- partial-update preservation ----

    def test_partial_payload_preserves_omitted_fields(self):
        self.encounter.transcript = 'preserved transcript'
        self.encounter.save()

        url = f'/api/patient/{self.patient.id}/encounter/{self.encounter.id}'
        # Only note is sent — transcript / recorder_status must NOT be nulled.
        resp = self.client.patch(
            url, data=json.dumps({'note': 'note only'}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)

        self.encounter.refresh_from_db()
        self.assertEqual(self.encounter.note, 'note only')
        self.assertEqual(self.encounter.transcript, 'preserved transcript')
        self.assertEqual(self.encounter.recorder_status, 0)

    # ---- 404 paths ----

    def test_returns_404_for_unknown_encounter(self):
        url = f'/api/patient/{self.patient.id}/encounter/99999'
        resp = self.client.patch(
            url, data=json.dumps({'note': 'x'}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 404)

    def test_returns_404_when_encounter_belongs_to_a_different_patient(self):
        # Encounter ownership is enforced by matching encounter_id + patient_id
        # together: if you request "patient B's encounter A", you get 404 even
        # though the encounter exists.
        url = f'/api/patient/{self.other_patient.id}/encounter/{self.encounter.id}'
        resp = self.client.patch(
            url, data=json.dumps({'note': 'should not write'}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 404)

        self.encounter.refresh_from_db()
        self.assertEqual(self.encounter.note, 'initial')

    # ---- auth ----

    def test_unauthenticated_request_redirects_to_login(self):
        self.client.logout()
        url = f'/api/patient/{self.patient.id}/encounter/{self.encounter.id}'
        resp = self.client.patch(
            url, data=json.dumps({'note': 'x'}),
            content_type='application/json',
        )
        # @login_required redirects (302) anonymous requests by default.
        self.assertIn(resp.status_code, (302, 401, 403))

    # ---- method gate ----

    def test_get_returns_405(self):
        url = f'/api/patient/{self.patient.id}/encounter/{self.encounter.id}'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 405)


class MobileCreateEncounterTests(TestCase):
    """Tests for the text-only encounter create endpoint. Used when iOS has
    recording disabled (events-only mode) so the encounter still reaches the
    server and joins the standard update pipeline."""

    def setUp(self):
        self.physician = User.objects.create_user(
            username='doc_a', password='top_secret',
            email='doc_a@example.com',
        )
        self.patient = User.objects.create_user(
            username='pt_a', password='unused',
            email='pt_a@example.com',
        )
        self.client = Client()
        self.client.login(username='doc_a', password='top_secret')

    def test_creates_encounter_with_all_fields(self):
        url = f'/api/patient/{self.patient.id}/encounter'
        body = {
            'start_time': '2026-06-04T12:00:00Z',
            'stop_time': '2026-06-04T12:15:00Z',
            'note': 'events only',
            'recorder_status': 2,
        }
        resp = self.client.post(url, data=json.dumps(body), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertTrue(data['success'])
        self.assertIn('id', data)

        enc = Encounter.objects.get(id=data['id'])
        self.assertEqual(enc.patient_id, self.patient.id)
        self.assertEqual(enc.physician_id, self.physician.id)
        self.assertEqual(enc.note, 'events only')
        self.assertEqual(enc.recorder_status, 2)
        self.assertIsNotNone(enc.stoptime)
        # start_time honored even though the model uses auto_now_add.
        self.assertEqual(enc.starttime.year, 2026)
        self.assertEqual(enc.starttime.hour, 12)

    def test_creates_encounter_with_minimum_payload(self):
        url = f'/api/patient/{self.patient.id}/encounter'
        resp = self.client.post(url, data=json.dumps({}), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertTrue(data['success'])

        enc = Encounter.objects.get(id=data['id'])
        self.assertEqual(enc.note, '')
        self.assertEqual(enc.recorder_status, 2)
        self.assertIsNone(enc.stoptime)

    def test_returns_404_for_unknown_patient(self):
        url = '/api/patient/99999/encounter'
        resp = self.client.post(url, data=json.dumps({'note': 'x'}), content_type='application/json')
        self.assertEqual(resp.status_code, 404)

    def test_unauthenticated_request_redirects_to_login(self):
        self.client.logout()
        url = f'/api/patient/{self.patient.id}/encounter'
        resp = self.client.post(url, data=json.dumps({'note': 'x'}), content_type='application/json')
        self.assertIn(resp.status_code, (302, 401, 403))

    def test_get_returns_405(self):
        url = f'/api/patient/{self.patient.id}/encounter'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 405)


class MobileEncounterClientUuidIdempotencyTests(TestCase):
    """The client_uuid contract: retrying a POST or PATCH with the same
    client_uuid must NOT create a duplicate row. This is what protects clinical
    data from network-blip retries — the only structural guard between a
    flaky push and silently-doubled encounters in the chart."""

    def setUp(self):
        self.physician = User.objects.create_user(
            username='doc_a', password='top_secret', email='doc_a@example.com',
        )
        self.patient = User.objects.create_user(
            username='pt_a', password='unused', email='pt_a@example.com',
        )
        self.client = Client()
        self.client.login(username='doc_a', password='top_secret')
        self.url = f'/api/patient/{self.patient.id}/encounter'

    def test_repeat_create_with_same_client_uuid_returns_same_row(self):
        body = {
            'client_uuid': '11111111-2222-3333-4444-555555555555',
            'note': 'first call',
        }
        first = self.client.post(self.url, data=json.dumps(body),
                                 content_type='application/json')
        self.assertEqual(first.status_code, 200)
        first_id = json.loads(first.content)['id']

        # Same client_uuid, different note — should UPDATE the existing row,
        # not create a new one.
        body['note'] = 'retry'
        second = self.client.post(self.url, data=json.dumps(body),
                                  content_type='application/json')
        self.assertEqual(second.status_code, 200)
        second_id = json.loads(second.content)['id']

        self.assertEqual(first_id, second_id)
        self.assertEqual(Encounter.objects.filter(patient=self.patient).count(), 1)
        enc = Encounter.objects.get(id=first_id)
        self.assertEqual(enc.note, 'retry')

    def test_event_client_uuid_dedup_on_repeat_patch(self):
        # Create the encounter first.
        enc = Encounter.objects.create(
            physician=self.physician, patient=self.patient,
            client_uuid='aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        )
        url = f'/api/patient/{self.patient.id}/encounter/{enc.id}'

        body = {
            'events': [
                {'client_uuid': 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
                 'summary': 'Started', 'offset_string': '00:00', 'is_favorite': False,
                 'datetime': '2026-06-04T20:00:00Z'},
                {'client_uuid': 'cccccccc-cccc-cccc-cccc-cccccccccccc',
                 'summary': 'Reviewed', 'offset_string': '00:30', 'is_favorite': False,
                 'datetime': '2026-06-04T20:00:30Z'},
            ],
        }
        first = self.client.patch(url, data=json.dumps(body),
                                  content_type='application/json')
        self.assertEqual(first.status_code, 200)
        first_events = {m['sync_id']: m['id'] for m in json.loads(first.content)['events']}
        self.assertEqual(len(first_events), 2)
        self.assertEqual(EncounterEvent.objects.filter(encounter=enc).count(), 2)

        # Retry the SAME PATCH — must not create duplicate events; must return
        # the same server IDs keyed by sync_id.
        second = self.client.patch(url, data=json.dumps(body),
                                   content_type='application/json')
        self.assertEqual(second.status_code, 200)
        second_events = {m['sync_id']: m['id'] for m in json.loads(second.content)['events']}
        self.assertEqual(first_events, second_events)
        self.assertEqual(EncounterEvent.objects.filter(encounter=enc).count(), 2)


class MobileEncounterRelationshipsAndEventsTests(TestCase):
    """Covers the new push-side fields: problem_ids, todo_ids,
    observation_value_ids, events. Verifies replace-by-snapshot semantics for
    relationships and defensive partial preservation when keys are absent."""

    def setUp(self):
        self.physician = User.objects.create_user(
            username='doc_a', password='top_secret', email='doc_a@example.com',
        )
        self.patient = User.objects.create_user(
            username='pt_a', password='unused', email='pt_a@example.com',
        )
        self.client = Client()
        self.client.login(username='doc_a', password='top_secret')

        self.p1 = Problem.objects.create(patient=self.patient, problem_name='P1')
        self.p2 = Problem.objects.create(patient=self.patient, problem_name='P2')
        self.t1 = ToDo.objects.create(patient=self.patient, todo='T1')

        self.obs = Observation.objects.create(name='Heart rate', code='8867-4')
        self.comp = ObservationComponent.objects.create(observation=self.obs, name='HR', component_code='8867-4')
        self.ov1 = ObservationValue.objects.create(component=self.comp, value_quantity='80')

        self.enc = Encounter.objects.create(
            physician=self.physician, patient=self.patient,
            client_uuid='dddddddd-dddd-dddd-dddd-dddddddddddd',
        )
        self.url = f'/api/patient/{self.patient.id}/encounter/{self.enc.id}'

    def test_patch_with_relationships_replaces_links(self):
        body = {
            'problem_ids': [self.p1.id, self.p2.id],
            'todo_ids': [self.t1.id],
            'observation_value_ids': [self.ov1.id],
        }
        resp = self.client.patch(self.url, data=json.dumps(body),
                                 content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(EncounterProblemRecord.objects.filter(encounter=self.enc).count(), 2)
        self.assertEqual(EncounterTodoRecord.objects.filter(encounter=self.enc).count(), 1)
        self.assertEqual(EncounterObservationValue.objects.filter(encounter=self.enc).count(), 1)

        # Second PATCH with a shrunken list REPLACES, not appends.
        body2 = {'problem_ids': [self.p1.id]}
        resp2 = self.client.patch(self.url, data=json.dumps(body2),
                                  content_type='application/json')
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(EncounterProblemRecord.objects.filter(encounter=self.enc).count(), 1)
        # Defensive partial: todo_ids was NOT in body2, so existing link stays.
        self.assertEqual(EncounterTodoRecord.objects.filter(encounter=self.enc).count(), 1)
        self.assertEqual(EncounterObservationValue.objects.filter(encounter=self.enc).count(), 1)

    def test_patch_with_empty_relationship_list_clears_links(self):
        EncounterProblemRecord.objects.create(encounter=self.enc, problem=self.p1)
        EncounterProblemRecord.objects.create(encounter=self.enc, problem=self.p2)

        # Empty list (key present) → wipe.
        resp = self.client.patch(self.url, data=json.dumps({'problem_ids': []}),
                                 content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(EncounterProblemRecord.objects.filter(encounter=self.enc).count(), 0)

    def test_absent_relationship_key_preserves_existing(self):
        EncounterProblemRecord.objects.create(encounter=self.enc, problem=self.p1)

        # Note-only PATCH — no relationship keys — must NOT wipe the existing
        # problem link. This is the load-bearing safety in the contract.
        resp = self.client.patch(self.url,
                                 data=json.dumps({'note': 'just a note edit'}),
                                 content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(EncounterProblemRecord.objects.filter(encounter=self.enc).count(), 1)

    def test_events_response_returns_sync_id_mapping(self):
        body = {
            'events': [
                {'client_uuid': 'eeeeeeee-1111-1111-1111-eeeeeeeeeeee',
                 'summary': 'Started', 'offset_string': '00:00', 'is_favorite': False,
                 'datetime': '2026-06-04T20:00:00Z'},
            ],
        }
        resp = self.client.patch(self.url, data=json.dumps(body),
                                 content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIn('events', data)
        self.assertEqual(len(data['events']), 1)
        mapping = data['events'][0]
        self.assertEqual(mapping['sync_id'], 'eeeeeeee-1111-1111-1111-eeeeeeeeeeee')
        self.assertTrue(isinstance(mapping['id'], int) and mapping['id'] > 0)

        ev = EncounterEvent.objects.get(id=mapping['id'])
        self.assertEqual(str(ev.client_uuid), 'eeeeeeee-1111-1111-1111-eeeeeeeeeeee')
        self.assertEqual(ev.summary, 'Started')
        self.assertEqual(ev.encounter_id, self.enc.id)

    def test_event_datetime_honors_client_time_not_server_auto_now(self):
        """The EncounterEvent.datetime model field has auto_now_add=True, which
        would stamp server-time on insert and collapse every event in a single
        PATCH batch to near-identical timestamps. The serializer derives
        offset_string from (event.datetime - encounter.starttime), so without
        the explicit override every event in a batch displays the same offset
        on Mac B. This regression test pins down the override."""
        body = {
            'events': [
                {'client_uuid': 'aaaa1111-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
                 'summary': 'Started', 'offset_string': '00:00', 'is_favorite': False,
                 'datetime': '2026-06-04T20:00:00Z'},
                {'client_uuid': 'aaaa2222-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
                 'summary': 'Reviewed', 'offset_string': '00:03', 'is_favorite': False,
                 'datetime': '2026-06-04T20:00:03Z'},
                {'client_uuid': 'aaaa3333-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
                 'summary': 'Stopped', 'offset_string': '00:18', 'is_favorite': False,
                 'datetime': '2026-06-04T20:00:18Z'},
            ],
        }
        resp = self.client.patch(self.url, data=json.dumps(body),
                                 content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        # Each event's stored datetime must match what the client sent — NOT
        # the moment the row was inserted server-side.
        events = EncounterEvent.objects.filter(encounter=self.enc).order_by('datetime')
        self.assertEqual(events.count(), 3)
        self.assertEqual(events[0].datetime.isoformat()[:19], '2026-06-04T20:00:00')
        self.assertEqual(events[1].datetime.isoformat()[:19], '2026-06-04T20:00:03')
        self.assertEqual(events[2].datetime.isoformat()[:19], '2026-06-04T20:00:18')

    def test_event_without_client_uuid_is_skipped(self):
        body = {
            'events': [
                {'summary': 'No UUID', 'offset_string': '00:00', 'is_favorite': False},
            ],
        }
        resp = self.client.patch(self.url, data=json.dumps(body),
                                 content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        # Skipped, not errored.
        self.assertEqual(json.loads(resp.content)['events'], [])
        self.assertEqual(EncounterEvent.objects.filter(encounter=self.enc).count(), 0)


class MobileUpdateProblemNoteTests(TestCase):
    """PATCH/DELETE for ProblemNote — covers the Bug-B-style server-authoritative
    audit emit and the client-treats-404-as-success delete contract that the
    macOS soft-delete sync depends on for idempotent retry."""

    def setUp(self):
        self.physician = User.objects.create_user(
            username='doc_a', password='top_secret',
            email='doc_a@example.com',
        )
        self.patient = User.objects.create_user(
            username='pt_a', password='unused',
            email='pt_a@example.com',
        )
        self.problem = Problem.objects.create(
            patient=self.patient,
            problem_name='Test problem',
            is_active=True,
            is_controlled=False,
        )
        self.note = ProblemNote.objects.create(
            problem=self.problem,
            author=self.physician,
            note='Initial note',
            note_type='wiki',
        )
        self.client = Client()
        self.client.login(username='doc_a', password='top_secret')

    def _url(self, note_id=None):
        nid = note_id if note_id is not None else self.note.id
        return f'/api/patient/{self.patient.id}/problem/{self.problem.id}/note/{nid}'

    # ---- PATCH ----

    def test_patch_updates_content_and_type(self):
        resp = self.client.patch(
            self._url(),
            data=json.dumps({'note': 'Updated content', 'note_type': 'history'}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(json.loads(resp.content)['success'])
        self.note.refresh_from_db()
        self.assertEqual(self.note.note, 'Updated content')
        self.assertEqual(self.note.note_type, 'history')

    def test_patch_partial_payload_preserves_omitted_field(self):
        resp = self.client.patch(
            self._url(),
            data=json.dumps({'note': 'Only content changed'}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        self.note.refresh_from_db()
        self.assertEqual(self.note.note, 'Only content changed')
        self.assertEqual(self.note.note_type, 'wiki')  # unchanged

    def test_patch_emits_note_edited_activity(self):
        before = ProblemActivity.objects.filter(problem=self.problem).count()
        resp = self.client.patch(
            self._url(),
            data=json.dumps({'note': 'Updated content'}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        after = ProblemActivity.objects.filter(problem=self.problem).count()
        self.assertEqual(after, before + 1)
        activity = ProblemActivity.objects.filter(problem=self.problem).order_by('-id').first()
        self.assertIn('Edited wiki note', activity.activity)
        self.assertIn('Updated content', activity.activity)
        self.assertEqual(activity.author_id, self.physician.id)

    def test_patch_rejects_empty_content(self):
        resp = self.client.patch(
            self._url(),
            data=json.dumps({'note': '   '}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)
        self.note.refresh_from_db()
        self.assertEqual(self.note.note, 'Initial note')

    def test_patch_requires_at_least_one_field(self):
        resp = self.client.patch(
            self._url(),
            data=json.dumps({}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)

    def test_patch_unauthorized_patient_id_404(self):
        # Wrong patient_id in the URL chain — auth join must reject.
        other = User.objects.create_user(
            username='pt_b', password='unused', email='pt_b@example.com',
        )
        url = f'/api/patient/{other.id}/problem/{self.problem.id}/note/{self.note.id}'
        resp = self.client.patch(
            url,
            data=json.dumps({'note': 'should fail'}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 404)
        self.note.refresh_from_db()
        self.assertEqual(self.note.note, 'Initial note')

    def test_patch_truncates_long_content_in_audit(self):
        long_content = 'A' * 500
        resp = self.client.patch(
            self._url(),
            data=json.dumps({'note': long_content}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        activity = ProblemActivity.objects.filter(problem=self.problem).order_by('-id').first()
        # Truncated to 200 chars + ellipsis. 201 A's in a row would mean we
        # exceeded the cap, so assert that's NOT present.
        self.assertIn('A' * 200 + '...', activity.activity)
        self.assertNotIn('A' * 201, activity.activity)

    def test_patch_accepts_note_type_only_change(self):
        resp = self.client.patch(
            self._url(),
            data=json.dumps({'note_type': 'history'}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        self.note.refresh_from_db()
        self.assertEqual(self.note.note_type, 'history')
        self.assertEqual(self.note.note, 'Initial note')

    # ---- DELETE ----

    def test_delete_removes_note_and_emits_activity(self):
        resp = self.client.delete(self._url())
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(json.loads(resp.content)['success'])
        self.assertFalse(ProblemNote.objects.filter(id=self.note.id).exists())
        activity = ProblemActivity.objects.filter(problem=self.problem).order_by('-id').first()
        self.assertIn('Deleted wiki note', activity.activity)
        self.assertIn('Initial note', activity.activity)
        self.assertEqual(activity.author_id, self.physician.id)

    def test_delete_already_gone_is_success_for_retry_idempotency(self):
        # First delete — succeeds normally.
        self.client.delete(self._url())
        # Second delete — note already gone. Must return 200 success so the
        # macOS client's retry-on-lost-response path doesn't strand a soft-
        # deleted row in the queue forever.
        resp = self.client.delete(self._url())
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(json.loads(resp.content)['success'])

    def test_delete_wrong_patient_chain_is_idempotent_noop(self):
        other = User.objects.create_user(
            username='pt_b', password='unused', email='pt_b@example.com',
        )
        url = f'/api/patient/{other.id}/problem/{self.problem.id}/note/{self.note.id}'
        # DELETE on a wrong patient URL collapses into the same "DoesNotExist
        # under this join" code path as a genuinely-gone note. We return 200
        # success (info-hiding from probe attempts) and the note must NOT be
        # deleted. A legitimate client never constructs this URL — the remoteID
        # was nested under the correct patient/problem in the pull response.
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(ProblemNote.objects.filter(id=self.note.id).exists())

    def test_method_not_allowed_returns_405(self):
        resp = self.client.get(self._url())
        self.assertEqual(resp.status_code, 405)


# ============================================================================
# PR-3: Observation parent (note), ObservationValue, ObservationPin
# ============================================================================


class _ObservationTestBase(TestCase):
    """Shared seed: one physician, one patient, one observation with a
    single component + initial value, no pins. Subclasses can attach pins
    via `pin_to(problem)` to exercise the fan-out audit path."""

    def setUp(self):
        self.physician = User.objects.create_user(
            username='doc_a', password='top_secret', email='doc_a@example.com',
        )
        self.patient = User.objects.create_user(
            username='pt_a', password='unused', email='pt_a@example.com',
        )
        self.observation = Observation.objects.create(
            name='Heart Rate', subject=self.patient,
        )
        self.component = ObservationComponent.objects.create(
            name='HR', observation=self.observation,
        )
        self.value = ObservationValue.objects.create(
            component=self.component, value_quantity=72, value_unit='bpm',
            author=self.physician,
        )
        self.client = Client()
        self.client.login(username='doc_a', password='top_secret')

    def pin_to(self, problem):
        return ObservationPinToProblem.objects.create(
            observation=self.observation, problem=problem, author=self.physician,
        )


class MobileUpdateObservationTests(_ObservationTestBase):
    """PATCH parent observation comments ("note") field — repurposes the
    dormant `comments` column rather than adding a new field."""

    def _url(self, obs_id=None):
        oid = obs_id if obs_id is not None else self.observation.id
        return f'/api/patient/{self.patient.id}/observation/{oid}'

    def test_patch_sets_comments_field(self):
        resp = self.client.patch(
            self._url(),
            data=json.dumps({'comments': 'Left arm, sitting'}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        self.observation.refresh_from_db()
        self.assertEqual(self.observation.comments, 'Left arm, sitting')

    def test_patch_empty_string_clears_to_null(self):
        # Setting "" stores as null so a re-pull doesn't echo back a phantom
        # empty-string the preserveLocal guard would treat as a server edit.
        self.observation.comments = 'old note'
        self.observation.save()
        resp = self.client.patch(
            self._url(),
            data=json.dumps({'comments': ''}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        self.observation.refresh_from_db()
        self.assertIsNone(self.observation.comments)

    def test_patch_explicit_null_clears(self):
        self.observation.comments = 'old note'
        self.observation.save()
        resp = self.client.patch(
            self._url(),
            data=json.dumps({'comments': None}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        self.observation.refresh_from_db()
        self.assertIsNone(self.observation.comments)

    def test_patch_missing_field_400(self):
        resp = self.client.patch(
            self._url(),
            data=json.dumps({}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)

    def test_patch_wrong_patient_404(self):
        other = User.objects.create_user(
            username='pt_b', password='unused', email='pt_b@example.com',
        )
        url = f'/api/patient/{other.id}/observation/{self.observation.id}'
        resp = self.client.patch(
            url, data=json.dumps({'comments': 'x'}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 404)

    def test_patch_audit_fans_out_to_every_pinned_problem(self):
        problem_a = Problem.objects.create(patient=self.patient, problem_name='Hypertension')
        problem_b = Problem.objects.create(patient=self.patient, problem_name='Atrial fibrillation')
        self.pin_to(problem_a)
        self.pin_to(problem_b)

        before_a = ProblemActivity.objects.filter(problem=problem_a).count()
        before_b = ProblemActivity.objects.filter(problem=problem_b).count()

        resp = self.client.patch(
            self._url(),
            data=json.dumps({'comments': 'Pulse check sitting'}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)

        # One audit row on each pinned problem.
        self.assertEqual(
            ProblemActivity.objects.filter(problem=problem_a).count(), before_a + 1
        )
        self.assertEqual(
            ProblemActivity.objects.filter(problem=problem_b).count(), before_b + 1
        )
        latest_a = ProblemActivity.objects.filter(problem=problem_a).order_by('-id').first()
        self.assertIn('Edited note', latest_a.activity)
        self.assertIn('Pulse check sitting', latest_a.activity)

    def test_patch_audit_unpinned_observation_uses_null_problem(self):
        # No pins. The legal trail goes to ProblemActivity(problem=None).
        before = ProblemActivity.objects.filter(problem__isnull=True).count()
        resp = self.client.patch(
            self._url(),
            data=json.dumps({'comments': 'No-pin note'}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        after = ProblemActivity.objects.filter(problem__isnull=True).count()
        self.assertEqual(after, before + 1)
        latest = (
            ProblemActivity.objects.filter(problem__isnull=True)
            .order_by('-id').first()
        )
        self.assertIn('No-pin note', latest.activity)

    def test_patch_audit_truncated_to_200_chars(self):
        problem = Problem.objects.create(patient=self.patient, problem_name='P1')
        self.pin_to(problem)
        long = 'X' * 500
        resp = self.client.patch(
            self._url(),
            data=json.dumps({'comments': long}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        latest = ProblemActivity.objects.filter(problem=problem).order_by('-id').first()
        self.assertIn('X' * 200 + '...', latest.activity)
        self.assertNotIn('X' * 201, latest.activity)


class MobileUpdateObservationValueTests(_ObservationTestBase):
    """PATCH + DELETE for an individual ObservationValue row."""

    def _url(self, vid=None):
        vid = vid if vid is not None else self.value.id
        return f'/api/patient/{self.patient.id}/observation/value/{vid}'

    def test_patch_updates_quantity(self):
        resp = self.client.patch(
            self._url(),
            data=json.dumps({'value_quantity': 88}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        self.value.refresh_from_db()
        self.assertEqual(float(self.value.value_quantity), 88.0)

    def test_patch_missing_field_400(self):
        resp = self.client.patch(
            self._url(),
            data=json.dumps({}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)

    def test_patch_quantity_null_400(self):
        resp = self.client.patch(
            self._url(),
            data=json.dumps({'value_quantity': None}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)

    def test_patch_audit_fans_out_to_pins(self):
        p1 = Problem.objects.create(patient=self.patient, problem_name='P1')
        p2 = Problem.objects.create(patient=self.patient, problem_name='P2')
        self.pin_to(p1)
        self.pin_to(p2)
        resp = self.client.patch(
            self._url(),
            data=json.dumps({'value_quantity': 99}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        latest_p1 = ProblemActivity.objects.filter(problem=p1).order_by('-id').first()
        latest_p2 = ProblemActivity.objects.filter(problem=p2).order_by('-id').first()
        self.assertIn('Edited Heart Rate reading', latest_p1.activity)
        self.assertIn('Edited Heart Rate reading', latest_p2.activity)

    def test_delete_removes_row_and_emits_audit(self):
        problem = Problem.objects.create(patient=self.patient, problem_name='P1')
        self.pin_to(problem)
        resp = self.client.delete(self._url())
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(ObservationValue.objects.filter(id=self.value.id).exists())
        latest = ProblemActivity.objects.filter(problem=problem).order_by('-id').first()
        self.assertIn('Deleted Heart Rate reading', latest.activity)

    def test_delete_already_gone_idempotent_success(self):
        # First delete actually removes the row.
        self.client.delete(self._url())
        # Second delete returns 200 success — matches the ProblemNote contract
        # from PR-1 so the macOS soft-delete queue can retry safely.
        resp = self.client.delete(self._url())
        self.assertEqual(resp.status_code, 200)

    def test_patch_wrong_patient_404(self):
        other = User.objects.create_user(
            username='pt_b', password='unused', email='pt_b@example.com',
        )
        url = f'/api/patient/{other.id}/observation/value/{self.value.id}'
        resp = self.client.patch(
            url, data=json.dumps({'value_quantity': 10}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 404)


class MobileObservationPinTests(_ObservationTestBase):
    """POST/DELETE on the URL-coordinate pin endpoint:
    /api/patient/<pid>/observation/<obs_id>/pin/<problem_id>"""

    def setUp(self):
        super().setUp()
        self.problem = Problem.objects.create(
            patient=self.patient, problem_name='Hypertension',
        )

    def _url(self, obs_id=None, prob_id=None):
        oid = obs_id if obs_id is not None else self.observation.id
        pid = prob_id if prob_id is not None else self.problem.id
        return f'/api/patient/{self.patient.id}/observation/{oid}/pin/{pid}'

    def test_post_creates_pin_and_emits_audit(self):
        resp = self.client.post(self._url())
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertTrue(data['success'])
        self.assertTrue(data['created'])
        self.assertTrue(
            ObservationPinToProblem.objects.filter(
                observation=self.observation, problem=self.problem,
            ).exists()
        )
        latest = ProblemActivity.objects.filter(problem=self.problem).order_by('-id').first()
        self.assertIn('Pinned Heart Rate', latest.activity)

    def test_post_idempotent_does_not_double_pin_or_double_audit(self):
        # First POST creates.
        self.client.post(self._url())
        audit_count_after_first = ProblemActivity.objects.filter(problem=self.problem).count()
        # Second POST is a no-op — no duplicate pin row, no duplicate audit row.
        resp = self.client.post(self._url())
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertFalse(data['created'])
        self.assertEqual(
            ObservationPinToProblem.objects.filter(
                observation=self.observation, problem=self.problem,
            ).count(),
            1,
        )
        self.assertEqual(
            ProblemActivity.objects.filter(problem=self.problem).count(),
            audit_count_after_first,
        )

    def test_delete_removes_pin_and_emits_audit(self):
        pin = self.pin_to(self.problem)
        resp = self.client.delete(self._url())
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(ObservationPinToProblem.objects.filter(id=pin.id).exists())
        latest = ProblemActivity.objects.filter(problem=self.problem).order_by('-id').first()
        self.assertIn('Unpinned Heart Rate', latest.activity)

    def test_delete_already_gone_idempotent_success_no_audit(self):
        # No pin exists. DELETE should still 200 success but not emit a
        # phantom "Unpinned" audit row.
        before = ProblemActivity.objects.filter(problem=self.problem).count()
        resp = self.client.delete(self._url())
        self.assertEqual(resp.status_code, 200)
        after = ProblemActivity.objects.filter(problem=self.problem).count()
        self.assertEqual(after, before)

    def test_post_wrong_patient_observation_404(self):
        other = User.objects.create_user(
            username='pt_b', password='unused', email='pt_b@example.com',
        )
        url = f'/api/patient/{other.id}/observation/{self.observation.id}/pin/{self.problem.id}'
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 404)

    def test_post_wrong_patient_problem_404(self):
        other_pt = User.objects.create_user(
            username='pt_b', password='unused', email='pt_b@example.com',
        )
        other_problem = Problem.objects.create(patient=other_pt, problem_name='Other')
        url = f'/api/patient/{self.patient.id}/observation/{self.observation.id}/pin/{other_problem.id}'
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 404)


# ============================================================================
# PR-2: PHI-safe media proxies + ProblemImage upload/delete
# ============================================================================
#
# These tests cover three things in one go:
# 1. The new `_assert_patient_access` helper, exercised through every proxy.
# 2. RBAC regression on the previously-IDOR-vulnerable audio + document
#    proxies (`mobile_encounter_audio`, `mobile_document_file`).
# 3. The new image upload/delete endpoints + UUID-keyed GCS path.
#
# The patient/staff/team graph is the same across all classes — extracted to
# `_RBACTestBase` so each scenario set isn't reseeding it from scratch.


class _RBACTestBase(TestCase):
    """Seeds a role-typed user graph covering every branch of
    `_assert_patient_access`. Subclasses pick which requester to log in as."""

    def setUp(self):
        # The patient that test resources will belong to.
        self.patient = User.objects.create_user(
            username='pt_a', password='x', email='a@x.com',
        )
        UserProfile.objects.create(user=self.patient, role='patient')

        # Physician with a PatientController on `patient` -> has access.
        self.attending = User.objects.create_user(
            username='doc_a', password='top_secret', email='doc_a@x.com',
        )
        UserProfile.objects.create(user=self.attending, role='physician')
        PatientController.objects.create(
            patient=self.patient, physician=self.attending,
        )

        # Physician with no PatientController -> denied.
        self.stranger_doc = User.objects.create_user(
            username='doc_b', password='top_secret', email='doc_b@x.com',
        )
        UserProfile.objects.create(user=self.stranger_doc, role='physician')

        # Nurse on the attending's PhysicianTeam -> access via team traversal.
        self.team_nurse = User.objects.create_user(
            username='nurse_a', password='top_secret', email='n@x.com',
        )
        UserProfile.objects.create(user=self.team_nurse, role='nurse')
        PhysicianTeam.objects.create(
            physician=self.attending, member=self.team_nurse,
        )

        # Nurse on a different physician's team -> denied.
        self.stranger_nurse = User.objects.create_user(
            username='nurse_b', password='top_secret', email='n2@x.com',
        )
        UserProfile.objects.create(user=self.stranger_nurse, role='nurse')
        PhysicianTeam.objects.create(
            physician=self.stranger_doc, member=self.stranger_nurse,
        )

        # Other patient -> denied access to our test patient's resources.
        self.other_patient = User.objects.create_user(
            username='pt_b', password='top_secret', email='b@x.com',
        )
        UserProfile.objects.create(user=self.other_patient, role='patient')

        # Admin -> access.
        self.admin_user = User.objects.create_user(
            username='admin_a', password='top_secret', email='adm@x.com',
        )
        UserProfile.objects.create(user=self.admin_user, role='admin')

        # User with no UserProfile row -> denied (helper's AttributeError /
        # DoesNotExist branch).
        self.no_profile = User.objects.create_user(
            username='no_profile', password='top_secret', email='np@x.com',
        )

        self.client = Client()

    def _login(self, user, password='top_secret'):
        # Patient seed used `password='x'`; other roles use 'top_secret'.
        return self.client.login(
            username=user.username,
            password='x' if user == self.patient or user == self.other_patient else password,
        )


class MobileEncounterAudioProxyRBACTests(_RBACTestBase):
    """Regression coverage on the previously-IDOR `mobile_encounter_audio`.
    Before PR-2 (2026-06-08) any authenticated user could fetch any
    encounter's audio. Now `_assert_patient_access` gates every fetch."""

    def setUp(self):
        super().setUp()
        self.encounter = Encounter.objects.create(
            physician=self.attending,
            patient=self.patient,
            audio=SimpleUploadedFile('clip.m4a', b'fake-audio', content_type='audio/mp4'),
        )
        self.url = f'/api/media/encounter/{self.encounter.id}/audio'

    def test_attending_physician_can_fetch_audio(self):
        self.assertTrue(self._login(self.attending))
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_team_nurse_can_fetch_audio(self):
        self.assertTrue(self._login(self.team_nurse))
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_patient_self_can_fetch_audio(self):
        self.assertTrue(self._login(self.patient))
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_admin_can_fetch_audio(self):
        self.assertTrue(self._login(self.admin_user))
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_stranger_physician_404(self):
        self.assertTrue(self._login(self.stranger_doc))
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 404)

    def test_stranger_team_nurse_404(self):
        self.assertTrue(self._login(self.stranger_nurse))
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 404)

    def test_other_patient_404(self):
        self.assertTrue(self._login(self.other_patient))
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 404)

    def test_no_profile_user_404(self):
        self.assertTrue(self._login(self.no_profile))
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 404)


class MobileDocumentFileProxyRBACTests(_RBACTestBase):
    """Regression coverage on `mobile_document_file` — same RBAC trap as
    audio, plus the orphan-deny policy (patient=None -> 404, no exceptions
    even for the document author)."""

    def setUp(self):
        super().setUp()
        self.doc = Document.objects.create(
            document=SimpleUploadedFile('chart.pdf', b'fake-pdf', content_type='application/pdf'),
            document_name='chart.pdf',
            author=self.attending,
            patient=self.patient,
        )
        self.url = f'/api/media/document/{self.doc.id}/file'

    def test_attending_can_fetch_document(self):
        self.assertTrue(self._login(self.attending))
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_stranger_physician_404(self):
        self.assertTrue(self._login(self.stranger_doc))
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 404)

    def test_orphaned_document_404_even_for_author(self):
        # Orphan policy: if patient is None, NO ONE can fetch the binary —
        # not even the original uploading author. Fail-closed PHI hygiene.
        orphan = Document.objects.create(
            document=SimpleUploadedFile('orphan.pdf', b'fake', content_type='application/pdf'),
            document_name='orphan.pdf',
            author=self.attending,
            patient=None,
        )
        self.assertTrue(self._login(self.attending))
        resp = self.client.get(f'/api/media/document/{orphan.id}/file')
        self.assertEqual(resp.status_code, 404)


class MobileImageFileProxyRBACTests(_RBACTestBase):
    """New image proxy. Gated by `_assert_patient_access` from day one."""

    def setUp(self):
        super().setUp()
        self.problem = Problem.objects.create(patient=self.patient, problem_name='Lesion')
        self.image = PatientImage.objects.create(
            patient=self.patient,
            problem=self.problem,
            image=SimpleUploadedFile('photo.jpg', b'fake-jpeg', content_type='image/jpeg'),
            file_name='photo.jpg',
            author=self.attending,
        )
        self.url = f'/api/media/image/{self.image.id}'

    def test_attending_can_fetch_image(self):
        self.assertTrue(self._login(self.attending))
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_stranger_physician_404(self):
        self.assertTrue(self._login(self.stranger_doc))
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 404)

    def test_other_patient_404(self):
        self.assertTrue(self._login(self.other_patient))
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 404)

    def test_nonexistent_image_404(self):
        self.assertTrue(self._login(self.attending))
        resp = self.client.get('/api/media/image/999999')
        self.assertEqual(resp.status_code, 404)


class MobileUploadProblemImageTests(_RBACTestBase):
    """POST multipart -> PatientImage row + GCS object. Idempotent via
    `client_uuid`. PHI-gated by `_assert_patient_access`."""

    def setUp(self):
        super().setUp()
        self.problem = Problem.objects.create(patient=self.patient, problem_name='Lesion')
        self.url = f'/api/patient/{self.patient.id}/problem/{self.problem.id}/image'
        self.client_uuid = '11111111-1111-1111-1111-111111111111'

    def _multipart_body(self, **overrides):
        body = {
            'file': SimpleUploadedFile('shot.jpg', b'fake-jpeg', content_type='image/jpeg'),
            'client_uuid': self.client_uuid,
            'file_name': 'shot.jpg',
            'caption': 'left arm bruise',
            'image_width': '1024',
            'image_height': '768',
        }
        body.update(overrides)
        return body

    def test_post_creates_image_and_emits_audit(self):
        self.assertTrue(self._login(self.attending))
        before = ProblemActivity.objects.filter(problem=self.problem).count()

        resp = self.client.post(self.url, data=self._multipart_body())
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertTrue(data['success'])
        self.assertTrue(data['created'])

        img = PatientImage.objects.get(id=data['id'])
        self.assertEqual(img.caption, 'left arm bruise')
        self.assertEqual(img.file_name, 'shot.jpg')
        self.assertEqual(img.image_width, 1024)
        self.assertEqual(img.image_height, 768)
        self.assertEqual(img.author_id, self.attending.id)
        self.assertEqual(img.problem_id, self.problem.id)
        # Audit emitted on the problem.
        self.assertEqual(
            ProblemActivity.objects.filter(problem=self.problem).count(),
            before + 1,
        )
        latest = ProblemActivity.objects.filter(problem=self.problem).order_by('-id').first()
        self.assertIn('Added image', latest.activity)

    def test_post_uses_uuid_keyed_gcs_path(self):
        # PR-2 acceptance gate: GCS object path must NOT include patient or
        # problem IDs — those are PHI and would leak to raw infra logs.
        self.assertTrue(self._login(self.attending))
        resp = self.client.post(self.url, data=self._multipart_body())
        self.assertEqual(resp.status_code, 200)
        img = PatientImage.objects.get(id=json.loads(resp.content)['id'])
        # set_problem_image_path returns "images/<uuid>.jpg" — verify both halves.
        self.assertTrue(img.image.name.startswith('images/'))
        self.assertNotIn(str(self.patient.id), img.image.name)
        self.assertNotIn(str(self.problem.id), img.image.name)

    def test_post_idempotent_same_client_uuid(self):
        # Second POST with the same client_uuid returns the existing row id
        # and `created=False` — no duplicate PatientImage, no duplicate audit.
        self.assertTrue(self._login(self.attending))
        resp1 = self.client.post(self.url, data=self._multipart_body())
        first_id = json.loads(resp1.content)['id']

        audit_after_first = ProblemActivity.objects.filter(problem=self.problem).count()

        resp2 = self.client.post(self.url, data=self._multipart_body())
        self.assertEqual(resp2.status_code, 200)
        data2 = json.loads(resp2.content)
        self.assertEqual(data2['id'], first_id)
        self.assertFalse(data2['created'])
        self.assertEqual(
            PatientImage.objects.filter(problem=self.problem).count(), 1
        )
        self.assertEqual(
            ProblemActivity.objects.filter(problem=self.problem).count(),
            audit_after_first,
        )

    def test_post_missing_file_400(self):
        self.assertTrue(self._login(self.attending))
        body = self._multipart_body()
        body.pop('file')
        resp = self.client.post(self.url, data=body)
        self.assertEqual(resp.status_code, 400)

    def test_post_missing_client_uuid_400(self):
        self.assertTrue(self._login(self.attending))
        body = self._multipart_body()
        body.pop('client_uuid')
        resp = self.client.post(self.url, data=body)
        self.assertEqual(resp.status_code, 400)

    def test_post_stranger_physician_404(self):
        self.assertTrue(self._login(self.stranger_doc))
        resp = self.client.post(self.url, data=self._multipart_body())
        self.assertEqual(resp.status_code, 404)
        # No row leaked across the access gate.
        self.assertFalse(PatientImage.objects.filter(client_uuid=self.client_uuid).exists())

    def test_post_team_nurse_can_upload(self):
        self.assertTrue(self._login(self.team_nurse))
        resp = self.client.post(self.url, data=self._multipart_body())
        self.assertEqual(resp.status_code, 200)


class MobileDeleteProblemImageTests(_RBACTestBase):
    """DELETE -> removes the row + GCS object + emits audit. Idempotent."""

    def setUp(self):
        super().setUp()
        self.problem = Problem.objects.create(patient=self.patient, problem_name='Lesion')
        self.image = PatientImage.objects.create(
            patient=self.patient,
            problem=self.problem,
            image=SimpleUploadedFile('shot.jpg', b'fake-jpeg', content_type='image/jpeg'),
            file_name='shot.jpg',
            author=self.attending,
        )
        self.url = f'/api/patient/{self.patient.id}/image/{self.image.id}'

    def test_delete_removes_row_and_emits_audit(self):
        self.assertTrue(self._login(self.attending))
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(PatientImage.objects.filter(id=self.image.id).exists())
        latest = ProblemActivity.objects.filter(problem=self.problem).order_by('-id').first()
        self.assertIn('Removed image', latest.activity)
        self.assertIn('shot.jpg', latest.activity)

    def test_delete_already_gone_idempotent_success(self):
        self.assertTrue(self._login(self.attending))
        # First delete actually removes.
        self.client.delete(self.url)
        # Second delete -> 200 success because the soft-delete queue retry
        # contract requires it.
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_delete_stranger_physician_404_image_preserved(self):
        self.assertTrue(self._login(self.stranger_doc))
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, 404)
        # Critical: image row MUST NOT be deleted by an unauthorized DELETE.
        self.assertTrue(PatientImage.objects.filter(id=self.image.id).exists())

    def test_delete_wrong_patient_in_url_404(self):
        self.assertTrue(self._login(self.attending))
        # Attending has access to self.patient but the URL points the image
        # at the other patient — the (image_id, patient_id) join fails.
        # Idempotent-success path returns 200 because DoesNotExist on the
        # joined query collapses into "already gone" — matches the
        # contract used elsewhere. The image must NOT actually be deleted.
        # Set up the other-patient PatientController so the access gate
        # passes; the join itself is what saves us.
        PatientController.objects.create(
            patient=self.other_patient, physician=self.attending,
        )
        url = f'/api/patient/{self.other_patient.id}/image/{self.image.id}'
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, 200)
        # Image still exists under the correct patient.
        self.assertTrue(PatientImage.objects.filter(id=self.image.id).exists())


# ============================================================================
# PR-4: Document upload idempotency + delete + link CRUD
# ============================================================================


class MobileUploadDocumentPR4Tests(_RBACTestBase):
    """`mobile_upload_document` PR-4 upgrades: client_uuid required,
    get_or_create idempotency, UUID-keyed GCS path, audit emit, RBAC."""

    def setUp(self):
        super().setUp()
        self.url = f'/api/patient/{self.patient.id}/document/upload'
        self.client_uuid = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'

    def _body(self, **overrides):
        body = {
            'file': SimpleUploadedFile('chart.pdf', b'fake-pdf', content_type='application/pdf'),
            'client_uuid': self.client_uuid,
            'document_name': 'chart.pdf',
        }
        body.update(overrides)
        return body

    def test_upload_creates_document_and_emits_audit(self):
        self.assertTrue(self._login(self.attending))
        # At upload time, doc has no links → audit lands on problem=None.
        before = ProblemActivity.objects.filter(problem__isnull=True).count()
        resp = self.client.post(self.url, data=self._body())
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertTrue(data['success'])
        self.assertTrue(data['created'])
        doc = Document.objects.get(id=data['id'])
        self.assertEqual(doc.document_name, 'chart.pdf')
        self.assertEqual(doc.patient_id, self.patient.id)
        after = ProblemActivity.objects.filter(problem__isnull=True).count()
        self.assertEqual(after, before + 1)
        latest = (
            ProblemActivity.objects.filter(problem__isnull=True)
            .order_by('-id').first()
        )
        self.assertIn('Added document', latest.activity)
        self.assertIn('chart.pdf', latest.activity)

    def test_upload_uses_uuid_keyed_gcs_path(self):
        # PR-4 acceptance gate: GCS object path must NOT include the patient
        # id or the user-supplied filename.
        self.assertTrue(self._login(self.attending))
        resp = self.client.post(self.url, data=self._body())
        self.assertEqual(resp.status_code, 200)
        doc = Document.objects.get(id=json.loads(resp.content)['id'])
        self.assertTrue(doc.document.name.startswith('documents/'))
        self.assertTrue(doc.document.name.endswith('.pdf'))
        self.assertNotIn(str(self.patient.id), doc.document.name)
        self.assertNotIn('chart', doc.document.name)

    def test_upload_idempotent_same_client_uuid(self):
        self.assertTrue(self._login(self.attending))
        resp1 = self.client.post(self.url, data=self._body())
        first_id = json.loads(resp1.content)['id']
        audit_after_first = ProblemActivity.objects.filter(problem__isnull=True).count()
        resp2 = self.client.post(self.url, data=self._body())
        self.assertEqual(resp2.status_code, 200)
        data2 = json.loads(resp2.content)
        self.assertEqual(data2['id'], first_id)
        self.assertFalse(data2['created'])
        self.assertEqual(Document.objects.filter(client_uuid=self.client_uuid).count(), 1)
        # No duplicate audit row on retry.
        self.assertEqual(
            ProblemActivity.objects.filter(problem__isnull=True).count(),
            audit_after_first,
        )

    def test_upload_missing_client_uuid_400(self):
        self.assertTrue(self._login(self.attending))
        body = self._body()
        body.pop('client_uuid')
        resp = self.client.post(self.url, data=body)
        self.assertEqual(resp.status_code, 400)

    def test_upload_missing_file_400(self):
        self.assertTrue(self._login(self.attending))
        body = self._body()
        body.pop('file')
        resp = self.client.post(self.url, data=body)
        self.assertEqual(resp.status_code, 400)

    def test_upload_stranger_physician_404(self):
        self.assertTrue(self._login(self.stranger_doc))
        resp = self.client.post(self.url, data=self._body())
        self.assertEqual(resp.status_code, 404)
        self.assertFalse(Document.objects.filter(client_uuid=self.client_uuid).exists())


class MobileDeleteDocumentTests(_RBACTestBase):
    """DELETE -> removes Document + GCS object + cascades to link tables.
    Audit fans out across whatever problems the doc was linked to at
    delete-time; orphans land on problem=None."""

    def setUp(self):
        super().setUp()
        self.problem = Problem.objects.create(patient=self.patient, problem_name='P1')
        self.doc = Document.objects.create(
            document=SimpleUploadedFile('chart.pdf', b'fake-pdf', content_type='application/pdf'),
            document_name='chart.pdf',
            author=self.attending,
            patient=self.patient,
        )
        self.url = f'/api/patient/{self.patient.id}/document/{self.doc.id}'

    def test_delete_removes_doc_and_fans_out_audit_to_linked_problem(self):
        DocumentProblem.objects.create(document=self.doc, problem=self.problem, author=self.attending)
        self.assertTrue(self._login(self.attending))
        before = ProblemActivity.objects.filter(problem=self.problem).count()
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Document.objects.filter(id=self.doc.id).exists())
        # CASCADE wiped the link too.
        self.assertFalse(DocumentProblem.objects.filter(document_id=self.doc.id).exists())
        after = ProblemActivity.objects.filter(problem=self.problem).count()
        self.assertEqual(after, before + 1)
        latest = ProblemActivity.objects.filter(problem=self.problem).order_by('-id').first()
        self.assertIn('Removed document', latest.activity)
        self.assertIn('chart.pdf', latest.activity)

    def test_delete_orphan_document_audits_to_problem_None(self):
        self.assertTrue(self._login(self.attending))
        before = ProblemActivity.objects.filter(problem__isnull=True).count()
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, 200)
        after = ProblemActivity.objects.filter(problem__isnull=True).count()
        self.assertEqual(after, before + 1)

    def test_delete_already_gone_idempotent_success(self):
        self.assertTrue(self._login(self.attending))
        self.client.delete(self.url)
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(json.loads(resp.content)['success'])

    def test_delete_stranger_physician_404_doc_preserved(self):
        self.assertTrue(self._login(self.stranger_doc))
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(Document.objects.filter(id=self.doc.id).exists())


class MobileDocumentProblemLinkTests(_RBACTestBase):
    """POST/DELETE on `/api/patient/<pid>/document/<doc_id>/link/problem/<problem_id>`.
    URL-coordinate identity → POST is idempotent via get_or_create."""

    def setUp(self):
        super().setUp()
        self.problem = Problem.objects.create(patient=self.patient, problem_name='P1')
        self.doc = Document.objects.create(
            document=SimpleUploadedFile('chart.pdf', b'fake', content_type='application/pdf'),
            document_name='chart.pdf',
            author=self.attending,
            patient=self.patient,
        )
        self.url = f'/api/patient/{self.patient.id}/document/{self.doc.id}/link/problem/{self.problem.id}'

    def test_post_creates_link_and_emits_problem_scoped_audit(self):
        self.assertTrue(self._login(self.attending))
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertTrue(data['created'])
        self.assertTrue(DocumentProblem.objects.filter(document=self.doc, problem=self.problem).exists())
        latest = ProblemActivity.objects.filter(problem=self.problem).order_by('-id').first()
        self.assertIn('Linked document', latest.activity)

    def test_post_idempotent_no_double_link_no_double_audit(self):
        self.assertTrue(self._login(self.attending))
        self.client.post(self.url)
        audit_after_first = ProblemActivity.objects.filter(problem=self.problem).count()
        resp = self.client.post(self.url)
        data = json.loads(resp.content)
        self.assertFalse(data['created'])
        self.assertEqual(
            DocumentProblem.objects.filter(document=self.doc, problem=self.problem).count(),
            1,
        )
        self.assertEqual(
            ProblemActivity.objects.filter(problem=self.problem).count(),
            audit_after_first,
        )

    def test_delete_removes_link_and_emits_audit(self):
        DocumentProblem.objects.create(document=self.doc, problem=self.problem, author=self.attending)
        self.assertTrue(self._login(self.attending))
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(DocumentProblem.objects.filter(document=self.doc, problem=self.problem).exists())
        latest = ProblemActivity.objects.filter(problem=self.problem).order_by('-id').first()
        self.assertIn('Unlinked document', latest.activity)

    def test_delete_no_existing_link_no_audit_still_success(self):
        self.assertTrue(self._login(self.attending))
        before = ProblemActivity.objects.filter(problem=self.problem).count()
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, 200)
        after = ProblemActivity.objects.filter(problem=self.problem).count()
        self.assertEqual(after, before)

    def test_post_stranger_physician_404(self):
        self.assertTrue(self._login(self.stranger_doc))
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 404)


class MobileDocumentTodoLinkTests(_RBACTestBase):
    """Sibling of MobileDocumentProblemLinkTests for the todo link table.
    Audit goes to the todo's parent problem when present, else
    problem=None."""

    def setUp(self):
        super().setUp()
        self.problem = Problem.objects.create(patient=self.patient, problem_name='P1')
        self.todo_with_problem = ToDo.objects.create(
            todo='lab follow-up', patient=self.patient, problem=self.problem,
        )
        self.problemless_todo = ToDo.objects.create(
            todo='free-floating todo', patient=self.patient,
        )
        self.doc = Document.objects.create(
            document=SimpleUploadedFile('chart.pdf', b'fake', content_type='application/pdf'),
            document_name='chart.pdf',
            author=self.attending,
            patient=self.patient,
        )

    def _url(self, todo):
        return f'/api/patient/{self.patient.id}/document/{self.doc.id}/link/todo/{todo.id}'

    def test_post_creates_link_audit_on_todos_parent_problem(self):
        self.assertTrue(self._login(self.attending))
        resp = self.client.post(self._url(self.todo_with_problem))
        self.assertEqual(resp.status_code, 200)
        latest = ProblemActivity.objects.filter(problem=self.problem).order_by('-id').first()
        self.assertIn('Linked document to todo', latest.activity)

    def test_post_link_to_problemless_todo_audits_to_problem_None(self):
        self.assertTrue(self._login(self.attending))
        before = ProblemActivity.objects.filter(problem__isnull=True).count()
        resp = self.client.post(self._url(self.problemless_todo))
        self.assertEqual(resp.status_code, 200)
        after = ProblemActivity.objects.filter(problem__isnull=True).count()
        self.assertEqual(after, before + 1)

    def test_delete_removes_link_and_emits_audit(self):
        DocumentTodo.objects.create(document=self.doc, todo=self.todo_with_problem, author=self.attending)
        self.assertTrue(self._login(self.attending))
        resp = self.client.delete(self._url(self.todo_with_problem))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(DocumentTodo.objects.filter(document=self.doc, todo=self.todo_with_problem).exists())
        latest = ProblemActivity.objects.filter(problem=self.problem).order_by('-id').first()
        self.assertIn('Unlinked document from todo', latest.activity)

    def test_post_stranger_physician_404(self):
        self.assertTrue(self._login(self.stranger_doc))
        resp = self.client.post(self._url(self.todo_with_problem))
        self.assertEqual(resp.status_code, 404)
