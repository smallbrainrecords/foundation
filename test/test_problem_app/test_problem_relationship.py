"""
Test problem's relationships of patient as admin
"""
from test.common import build_driver, login, load_data, manage_patient, ADMIN_USER, PATIENT_USER
from test.test_problem_app.common import add_problem, show_problem, relate_problems
from django.test import LiveServerTestCase
from emr.models import User


class TestProblemRelationships(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        """
        Prepare environment before run the tests
        """
        super(TestProblemRelationships, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        """
        Clean up the environment and db after all tests have finished.
        """
        super(TestProblemRelationships, cls).tearDownClass()
        
    def test_problem_relationships(self):
        """
        Test add problem's relationships as admin.
        """
        try:
            # Prepare test
            load_data()
            driver = build_driver()
            
            problem_1 = 'Sickness'
            problem_2 = 'Headache'

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

            # Add problem 1
            add_problem(driver, problem_term=problem_1)
            
            # Add problem 2
            add_problem(driver, problem_term=problem_2)
            driver.refresh()
            
            # Go to problem 1
            show_problem(driver, problem_term=problem_1)
            
            # Create relationship with problem 1 and problem 2
            relate_problems(driver, problem_1=problem_1, problem_2=problem_2)
            
        finally:
            driver.quit()
    