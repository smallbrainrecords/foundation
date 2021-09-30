"""
Test proble's goals as admin
"""
from test.common import build_driver, login, load_data, manage_patient, ADMIN_USER, PATIENT_USER
from test.test_problem_app.common import add_problem, edit_problem_term, show_problem, add_problem_goal, view_problem_goal, add_goal_note, update_goal_status
from django.test import LiveServerTestCase
from emr.models import User


class TestProblemGoals(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        """
        Prepare environment before run the tests
        """
        super(TestProblemGoals, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        """
        Clean up the environment and db after all tests have finished.
        """
        super(TestProblemGoals, cls).tearDownClass()

    def test_problem_goals(self):
        """
        Test problem's goals as admin.
        """
        try:
            # Prepare test
            load_data()
            driver = build_driver()

            problem_term = 'Head Ache'
            problem_goal = 'Goal 1'
            problem_note = 'Note 1'

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
            add_problem(driver, problem_term=problem_term)

            driver.refresh()

            # Go to problem page
            show_problem(driver, problem_term=problem_term)

            # Add problem goals
            add_problem_goal(driver, goal=problem_goal)

            # View problem goal
            view_problem_goal(driver, goal=problem_goal)

            # Add note to goal
            add_goal_note(driver, note=problem_note)

            # Update goal's status
            update_goal_status(
                driver, currently_succeding=True, is_accomplished=True)
        finally:
            driver.quit()
