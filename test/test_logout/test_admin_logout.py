"""Test logout as admin"""
from test.common import build_driver, login, logout, load_data, ADMIN_USER
from django.test import LiveServerTestCase


class TestAdminLogout(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        """
        Prepare environment before run the tests
        """
        super(TestAdminLogout, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        """
        Clean up the environment and db after all tests have finished.
        """
        super(TestAdminLogout, cls).tearDownClass()

    def test_admin_logout(self):
        """
        Test logout as admin.
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

            # Logout as admin
            logout(driver)

            assert driver.current_url == self.live_server_url + \
                '/', 'Logout failed: user -> {}'.format(ADMIN_USER['username'])

            # Check redirect to login page
            driver.get(
                '{}/project/{}/#/'.format(self.live_server_url, ADMIN_USER['username']))

            assert driver.current_url == '{}/u/login/?next=/project/{}/#/'.format(
                self.live_server_url, ADMIN_USER['username']), 'Login redirect failed: user -> {}'.format(ADMIN_USER['username'])
        
        finally:
            driver.quit()
