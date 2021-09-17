"""
Test register mid level pa/np.
"""
from test.common import build_driver, login, register_user_by_admin, load_data, TEMP_MID_LEVEL_USER, ADMIN_USER
from django.test import LiveServerTestCase


class TestMidLevelRegister(LiveServerTestCase):
    """
    Register mid level pa/np test using an admin user.
    """
    @classmethod
    def setUpClass(cls):
        """
        Prepare environment before run the tests
        """
        super(TestMidLevelRegister, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        """
        Clean up the environment and db after all tests have finished.
        """
        super(TestMidLevelRegister, cls).tearDownClass()

    def test_register_mid_level(self):
        """
        Test register mid level pa/np using an admin user.
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

            # Register mid level
            register_user_by_admin(driver,
                                   first_name=TEMP_MID_LEVEL_USER['first_name'],
                                   last_name=TEMP_MID_LEVEL_USER['last_name'],
                                   username=TEMP_MID_LEVEL_USER['username'],
                                   email=TEMP_MID_LEVEL_USER['email'],
                                   role=TEMP_MID_LEVEL_USER['role'],
                                   password=TEMP_MID_LEVEL_USER['password'])

        finally:
            driver.quit()
