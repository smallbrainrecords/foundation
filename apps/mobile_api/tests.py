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

from emr.models import (
    Encounter, EncounterEvent,
    EncounterProblemRecord, EncounterTodoRecord, EncounterObservationValue,
    Problem, ToDo, Observation, ObservationComponent, ObservationValue,
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
