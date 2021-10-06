"""Test assing physician to patient"""
from test.common import build_driver, login, edit_patient, assing_physician_to_patient, load_data, PATIENT_USER, ADMIN_USER, PHYSICIAN_USER
from django.test import LiveServerTestCase


class TestAssingPhysician(LiveServerTestCase):
    """
    Manage patient test for patients using an admin user.
    """
    @classmethod
    def setUpClass(cls):
        """
        Prepare environment before run the tests
        """
        super(TestAssingPhysician, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        """
        Clean up the environment and db after all tests have finished.
        """
        super(TestAssingPhysician, cls).tearDownClass()

    def test_assing_physician_to_patient(self):
        """
        Test assing physician to patient using an admin user.
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

            # Edit patient.
            edit_patient(driver, PATIENT_USER['username'])

            assert str(driver.current_url).startswith('{}/project/{}/#/edit/'.format(
                self.live_server_url, ADMIN_USER['username'])), 'Edit patient failed: patient -> {}'.format(PATIENT_USER['username'])

            # Assing physician
            assing_physician_to_patient(driver,
                                        patient_username=PATIENT_USER['username'],
                                        physician_username=PHYSICIAN_USER['username'])

        finally:
            driver.quit()
