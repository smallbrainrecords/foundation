"""Test login as patient"""
from test.common import build_driver, login, load_data, PATIENT_USER
from django.test import LiveServerTestCase
from emr.models import User, UserProfile


class TestPatientLogin(LiveServerTestCase):
    """
    Login test as patient user.
    """
    @classmethod
    def setUpClass(cls):
        """
        Prepare environment before run the tests
        """
        super(TestPatientLogin, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        """
        Clean up the environment and db after all tests have finished.
        """
        super(TestPatientLogin, cls).tearDownClass()

    def test_patient_login(self):
        """
        Test login as patient user with correct credentials.
        """
        try:
            # Prepare test
            load_data()
            driver = build_driver()

            # Login as patient
            login(driver,
                  base_url=self.live_server_url,
                  username=PATIENT_USER['email'],
                  password=PATIENT_USER['password'])

            assert str(driver.current_url).startswith('{}/u/patient/manage/'.format(
                self.live_server_url)), 'Login failed: user -> {}, {}'.format(PATIENT_USER['username'], PATIENT_USER['password'])
        finally:
            driver.quit()

    def test_patient_login_with_incorrect_password(self):
        """
        Test login as patient user with incorrect password.
        """
        try:
            # Prepare test
            load_data()
            driver = build_driver()

            # Login test
            login(driver,
                  base_url=self.live_server_url,
                  username=PATIENT_USER['email'],
                  password=PATIENT_USER['password'] + 'xyz')

            assert driver.current_url == '{}/u/login/'.format(
                self.live_server_url), 'Login with incorrent password failed: user -> {}'.format(PATIENT_USER['username'])
        finally:
            driver.quit()
