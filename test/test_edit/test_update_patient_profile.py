"""
Test update patient profile using admin account.
"""
from test.common import build_driver, login, edit_patient, assing_physician_to_patient, update_basic_information, load_data, get_user, PATIENT_USER, ADMIN_USER, PHYSICIAN_USER
from django.test import LiveServerTestCase
from emr.models import User, UserProfile


class TestUpdatePatientProfile(LiveServerTestCase):
    """
    Update patient profile test using an admin user.
    """
    @classmethod
    def setUpClass(cls):
        """
        Prepare environment before run the tests
        """
        super(TestUpdatePatientProfile, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        """
        Clean up the environment and db after all tests have finished.
        """
        super(TestUpdatePatientProfile, cls).tearDownClass()

    def test_update_basic_information_of_patient(self):
        """
        Test update basic information of patient using an admin user.
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

            # Edit patient
            edit_patient(driver, PATIENT_USER['username'])

            assert str(driver.current_url).startswith('{}/project/{}/#/edit/'.format(
                self.live_server_url, ADMIN_USER['username'])), 'Edit patient failed: patient -> {}'.format(PATIENT_USER['username'])

            # Update basic information
            update_basic_information(
                driver, PATIENT_USER['first_name'] + ' updated', PATIENT_USER['last_name'] + ' updated')

            # Check result
            user = get_user(PATIENT_USER['username'])

            assert user, 'The patient \'{}\' is not found'.format(
                PATIENT_USER['username'])

            assert user.first_name == PATIENT_USER['first_name'] + \
                ' updated', 'First name of the patient hasn\'t been update failed'
            assert user.last_name == PATIENT_USER['last_name'] + \
                ' updated', 'Last name of the patient hasn\'t been update failed'

        finally:
            driver.quit()

    def test_update_profile_information_of_patient(self):
        """
        Test assign physician to patient user.
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

            # Edit patient
            edit_patient(driver, PATIENT_USER['username'])

            assert str(driver.current_url).startswith('{}/project/{}/#/edit/'.format(
                self.live_server_url, ADMIN_USER['username'])), 'Edit patient failed: patient -> {}'.format(PATIENT_USER['username'])
