"""Test login as admin"""
from test.common import build_driver, login, load_data, ADMIN_USER
from django.test import LiveServerTestCase
from emr.models import User, UserProfile


class TestAdminLogin(LiveServerTestCase):

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

    def test_admin_login(self):
        """
        Test login as admin with correct credentials.
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
        finally:
            driver.quit()

    def test_admin_login_with_incorrect_password(self):
        """
        Test login as admin with an incorrect password.
        """
        try:
            # Prepare test
            load_data()
            driver = build_driver()

            # Login as admin
            login(driver,
                  base_url=self.live_server_url,
                  username=ADMIN_USER['username'],
                  password=ADMIN_USER['password'] + 'xyz')

            assert driver.current_url == '{}/u/login/'.format(
                self.live_server_url), 'Login with incorrent password failed: user -> {}'.format(ADMIN_USER['username'])
        finally:
            driver.quit()
