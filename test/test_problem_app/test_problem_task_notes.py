"""
Test problem's taks, notes and status as admin.
"""
import unittest

from test.common import build_driver, login, load_data, manage_patient, ADMIN_USER, PATIENT_USER
from test.test_problem_app.common import add_problem, show_problem, add_task, add_note, update_status
from django.test import LiveServerTestCase


@unittest.skip("skip the test")
class TestProblemTaskNoteStatus(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        """
        Prepare environment before run the tests
        """
        super(TestProblemTaskNoteStatus, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        """
        Clean up the environment and db after all tests have finished.
        """
        super(TestProblemTaskNoteStatus, cls).tearDownClass()

    def test_problem_task_note_status(self):
        """
        Test problem's taks, notes and status as admin.
        """
        try:
            # Prepare test
            load_data()
            driver = build_driver()

            problem = 'Sickness'
            task = 'Task 1'
            note = 'Note 1'

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

            # Add problem
            add_problem(driver, problem_term=problem)
            driver.refresh()

            # Go to problem
            show_problem(driver, problem_term=problem)

            # Add task
            add_task(driver, task=task)

            # Add note
            add_note(driver, note=note)

        finally:
            driver.quit()
