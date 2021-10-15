"""Test login as patient"""
from test.common import build_driver, login, load_data, PATIENT_USER
from django.test import LiveServerTestCase


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
