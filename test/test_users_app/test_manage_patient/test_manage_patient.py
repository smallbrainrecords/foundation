"""Test manage patient"""
from test.common import build_driver, login, manage_patient, load_data, PATIENT_USER, ADMIN_USER
from django.test import LiveServerTestCase
from emr.models import User, UserProfile


class TestManagePatient(LiveServerTestCase):
    """
    Manage patient test for patients using an admin user.
    """
    @classmethod
    def setUpClass(cls):
        """
        Prepare environment before run the tests
        """
        super(TestManagePatient, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        """
        Clean up the environment and db after all tests have finished.
        """
        super(TestManagePatient, cls).tearDownClass()

    def test_manage_patient(self):
        """
        Test manage patient page using an admin user.
        """
        try:
            # Prepare test
            load_data()
            driver = build_driver()

            # Login as admin
            login(driver,
                  base_url=self.live_server_url,
                  username=ADMIN_USER['username'],
                  password=ADMIN_USER['password'])

            assert driver.current_url == '{}/project/{}/#/'.format(
                self.live_server_url, ADMIN_USER['username']), 'Login failed: user -> {}, {}'.format(ADMIN_USER['username'], ADMIN_USER['password'])

            # Manage patient
            manage_patient(driver, PATIENT_USER['username'])

            assert str(driver.current_url).startswith('{}/u/patient/manage/'.format(
                self.live_server_url)), 'Manage patient failed: patient -> {}'.format(PATIENT_USER['username'])

        finally:
            driver.quit()
