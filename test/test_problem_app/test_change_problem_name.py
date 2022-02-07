"""Test change problem's name as admin"""
import os
import shutil
import unittest

from test.common import build_driver, login, load_data, manage_patient, ADMIN_USER, PATIENT_USER
from test.test_problem_app.common import add_problem, edit_problem_term, show_problem
from django.test import LiveServerTestCase

src_dir = os.getcwd() + '/test/test_problem_app/problems.controller.js'
src_copy_dir = os.getcwd() + '/test/test_problem_app/problems.controller copy.js'
dst_dir = os.getcwd() + '/static/apps/patient/problem-page/problems.controller.js'


@unittest.skip("skip the test")
class TestChangeProblemNameLogin(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        """
        Prepare environment before run the tests
        """
        shutil.copyfile(src=src_dir, dst=dst_dir)
        super(TestChangeProblemNameLogin, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        """
        Clean up the environment and db after all tests have finished.
        """
        shutil.copyfile(src=src_copy_dir, dst=dst_dir)
        super(TestChangeProblemNameLogin, cls).tearDownClass()

    def test_change_problem_name(self):
        """
        Test change problem's name as physician.
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

            # Check results
            assert driver.current_url == '{}/project/{}/#/'.format(
                self.live_server_url, ADMIN_USER['username']), 'Login failed: user -> {}, {}'.format(ADMIN_USER['username'], ADMIN_USER['password'])

            # Manage patient
            manage_patient(driver, PATIENT_USER['username'])

            assert str(driver.current_url).startswith('{}/u/patient/manage/'.format(
                self.live_server_url)), 'Manage patient failed: patient -> {}'.format(PATIENT_USER['username'])

            # Add problem
            add_problem(driver, problem_term='Head Ache')

            driver.refresh()

            # Go to problem page
            show_problem(driver, problem_term='Head Ache')

            # Edit problem
            edit_problem_term(driver, new_problem_term='Head Ache 2')

        finally:
            driver.quit()
