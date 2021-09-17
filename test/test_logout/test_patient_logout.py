"""Test logout as patient"""
from test.common import build_driver, login, logout, load_data, PATIENT_USER
from django.test import LiveServerTestCase
from emr.models import User


class TestPatientLogout(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        """
        Prepare environment before run the tests
        """
        super(TestPatientLogout, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        """
        Clean up the environment and db after all tests have finished.
        """
        super(TestPatientLogout, cls).tearDownClass()

    def test_patient_logout(self):
        """
        Test logout as patient.
        """
        try:
            # Prepare test
            load_data()
            driver = build_driver()

            # Login as patient
            login(driver,
                  base_url=self.live_server_url,
                  username=PATIENT_USER['username'],
                  password=PATIENT_USER['password'])

            # Check results
            assert str(driver.current_url).startswith('{}/u/patient/manage/'.format(
                self.live_server_url)), 'Login failed: user -> {}, {}'.format(PATIENT_USER['username'], PATIENT_USER['password'])

            # Request Logout
            logout(driver, is_patient=True)

            assert driver.current_url == self.live_server_url + \
                '/', 'Logout failed: user -> {}'.format(
                    PATIENT_USER['username'])

            # Check redirect to login page
            user = User.objects.get(username=PATIENT_USER['username'])
            driver.get(
                '{}/u/patient/manage/{}/#/'.format(self.live_server_url, user.id))

            assert driver.current_url == '{}/u/login/?next=/u/patient/manage/{}/#/'.format(
                self.live_server_url, user.id), 'Login redirect failed: user -> {}'.format(PATIENT_USER['username'])

        finally:
            driver.quit()
