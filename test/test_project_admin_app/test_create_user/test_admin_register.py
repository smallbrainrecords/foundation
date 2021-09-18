"""
Test admin register using admin account
"""
from test.common import build_driver, login, register_user_by_admin, load_data, TEMP_ADMIN_USER, ADMIN_USER
from django.test import LiveServerTestCase


class TestAdminRegister(LiveServerTestCase):
    """
    Register admin test using an admin user.
    """
    @classmethod
    def setUpClass(cls):
        """
        Prepare environment before run the tests
        """
        super(TestAdminRegister, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        """
        Clean up the environment and db after all tests have finished.
        """
        super(TestAdminRegister, cls).tearDownClass()

    def test_register_admin(self):
        """
        Test register admin using an admin user.
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

            # Register admin
            register_user_by_admin(driver,
                                   first_name=TEMP_ADMIN_USER['first_name'],
                                   last_name=TEMP_ADMIN_USER['last_name'],
                                   username=TEMP_ADMIN_USER['username'],
                                   email=TEMP_ADMIN_USER['email'],
                                   role=TEMP_ADMIN_USER['role'],
                                   password=TEMP_ADMIN_USER['password'])

        finally:
            driver.quit()
