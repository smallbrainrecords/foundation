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

from emr.models import Encounter


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
        self.assertEqual(json.loads(resp.content), {'success': True})

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
