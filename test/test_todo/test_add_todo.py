"""Test add todo to patient"""
from test.common import build_driver, login, edit_patient, assing_physician_to_patient, manage_patient, add_todo, load_data, PATIENT_USER, ADMIN_USER, PHYSICIAN_USER
from django.test import LiveServerTestCase


class TestAddTodo(LiveServerTestCase):
    """
    Add ToDo to patient test using an admin user.
    """
    @classmethod
    def setUpClass(cls):
        """
        Prepare environment before run the tests
        """
        super(TestAddTodo, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        """
        Clean up the environment and db after all tests have finished.
        """
        super(TestAddTodo, cls).tearDownClass()

    def test_add_todo(self):
        """
        Test add todo to patient using an admin user.
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

            # Assing physician
            add_todo(driver,
                     username=PATIENT_USER['username'],
                     title='TODO TITLE')

        finally:
            driver.quit()

    def test_add_todo_with_tag(self):
        """
        Test add todo to patient and tag a physician using an admin user.
        """
        try:
            # Prepare test (part 1)
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

            driver.quit()

            # Prepare test (part 2)
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

            # Assing physician
            add_todo(driver,
                     username=PATIENT_USER['username'],
                     title='TODO TITLE',
                     physician_full_name=PHYSICIAN_USER['first_name'] + ' ' + PHYSICIAN_USER['last_name'])

        finally:
            driver.quit()