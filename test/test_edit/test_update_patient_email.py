"""Test update patient email"""
from test.common import build_driver, login, edit_patient, update_email, load_data, PATIENT_USER, ADMIN_USER
from django.test import LiveServerTestCase
from emr.models import User


class TestUpdatePatientEmail(LiveServerTestCase):
    """
    Update patient email test using an admin user.
    """
    @classmethod
    def setUpClass(cls):
        """
        Prepare environment before run the tests
        """
        super(TestUpdatePatientEmail, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        """
        Clean up the environment and db after all tests have finished.
        """
        super(TestUpdatePatientEmail, cls).tearDownClass()

    def test_update_email(self):
        """
        Test update patient email using an admin user.
        """
        try:
            # Prepare test
            load_data()
            driver = build_driver()
            new_email = 'temp-updated@mail.com'

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

            # Update email
            update_email(driver, new_email)

            # Check result
            user = User.objects.get(username=PATIENT_USER['username'])

            assert user, 'The patient \'{}\' is not found'.format(
                PATIENT_USER['username'])

            assert user.email == new_email, 'Email of the patient hasn\'t been updated failed.'

        finally:
            driver.quit()

    def test_update_email_already_in_use(self):
        """
        Test update patient's email (already used by other user) using an admin user.
        """
        try:
            # Prepare test
            load_data()
            driver = build_driver()
            new_email = ADMIN_USER['email']

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

            # Update email
            update_email(driver, new_email)

            # Check result
            user = User.objects.get(username=PATIENT_USER['username'])

            assert user, 'The patient \'{}\' is not found'.format(
                PATIENT_USER['username'])

            assert user.email == new_email, 'Email of the patient hasn\'t been updated for one email that is already in used.'

        finally:
            driver.quit()
