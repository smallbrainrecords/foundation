"""Test change problem's name as admin"""
from test.common import build_driver, login, load_data, ADMIN_USER, PATIENT_USER
from django.test import LiveServerTestCase
from emr.models import User, UserProfile


class TestChangeProblemNameLogin(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        """
        Prepare environment before run the tests
        """
        super(TestAdminLogin, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        """
        Clean up the environment and db after all tests have finished.
        """
        super(TestAdminLogin, cls).tearDownClass()

    def test_change_problem_name(self):
        """
        Test change problem's name as physician.
        """
        try:
            # Prepare test
            load_data()
            driver = build_driver()

            try:
            # Prepare test
            load_data()
            driver = build_driver()

            # Login as admin
            login(driver,
                  base_url=self.live_server_url,
                  username=ADMIN_USER['username'],
                  password=ADMIN_USER['password'])

            # Check results
            assert driver.current_url == '{}/project/{}/#/'.format(
                self.live_server_url, ADMIN_USER['username']), 'Login failed: user -> {}, {}'.format(ADMIN_USER['username'], ADMIN_USER['password'])

            # Manage patient
            manage_patient(driver, PATIENT_USER['username'])

            assert str(driver.current_url).startswith('{}/u/patient/manage/'.format(
                self.live_server_url)), 'Manage patient failed: patient -> {}'.format(PATIENT_USER['username'])

        finally:
            driver.quit()