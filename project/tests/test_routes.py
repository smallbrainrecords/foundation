"""What the server answers at all (2026-11-22).

The app is the only client. The retired web application's routes are not
mounted, and this list is how they stay that way.
"""
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import get_resolver

from emr.models import PatientController, UserProfile


class RouteTableTests(TestCase):
    MOUNTED = {
        '^$',
        '^api/',
        '^u/login/?$',
        r'^my_story/(?P<patient_id>\d+)/get_my_story$',
        '^session_security/',
    }

    def test_only_these_routes_are_mounted(self):
        self.assertEqual({str(p.pattern) for p in get_resolver().url_patterns}, self.MOUNTED)

    def test_retired_web_paths_are_gone_for_everyone(self):
        user = User.objects.create_user('someone', password='invented-pass-1')
        UserProfile.objects.create(user=user, role='admin')
        signed_in = Client()
        signed_in.force_login(user)
        paths = [
            '/u/register/', '/u/home/', '/register_users/', '/list_of_users/',
            '/project/admin/user/update/password/', '/get_problems/1/', '/change_status/',
            '/todo/attachment/1/downloadAttachment', '/p/problem/1/getproblems',
            '/update/', '/media/documents/x.pdf', '/docs/list', '/my_story/1/info',
        ]
        for path in paths:
            for client in (Client(), signed_in):
                with self.subTest(path=path):
                    self.assertEqual(client.get(path).status_code, 404)
                    self.assertEqual(client.post(path).status_code, 404)

    def test_the_sign_in_address_answers_signed_out(self):
        client = Client(enforce_csrf_checks=True)
        # 302 keeps the method for PATCH, PUT and DELETE.
        for response in (client.get('/u/login/?next=/api/patients/'), client.post('/u/login/'),
                         client.patch('/u/login/'), client.put('/u/login/'), client.delete('/u/login/')):
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.json()['error'], 'signed_out')

    def test_a_signed_out_app_request_ends_at_401(self):
        response = Client().get('/api/patients/', follow=True)
        self.assertEqual(response.status_code, 401)

    def test_signed_in_requests_still_pass_the_session_middleware(self):
        # SessionSecurityMiddleware reverses its ping URL from the second request on.
        user = User.objects.create_user('second_request', password='invented-pass-1')
        UserProfile.objects.create(user=user, role='patient')
        client = Client()
        client.force_login(user)
        for _ in range(3):
            self.assertEqual(client.get('/api/patients/').status_code, 200)

    def test_my_story_answers_only_for_the_chart(self):
        doctor = User.objects.create_user('story_doctor', password='invented-pass-1')
        UserProfile.objects.create(user=doctor, role='physician')
        patient = User.objects.create_user('story_patient', password='invented-pass-1')
        UserProfile.objects.create(user=patient, role='patient')
        other = User.objects.create_user('story_other', password='invented-pass-1')
        UserProfile.objects.create(user=other, role='patient')
        PatientController.objects.create(physician=doctor, patient=patient)
        url = '/my_story/%d/get_my_story' % patient.id
        for user, status in ((doctor, 200), (patient, 200), (other, 404)):
            client = Client()
            client.force_login(user)
            self.assertEqual(client.get(url).status_code, status, user.username)
        self.assertEqual(Client().get(url).status_code, 302)
