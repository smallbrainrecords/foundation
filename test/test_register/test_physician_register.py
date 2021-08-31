"""Test register physician"""
from test.common import build_driver, login, register_user_by_admin, load_data, TEMP_PHYSICIAN_USER, ADMIN_USER
from django.test import LiveServerTestCase
from emr.models import User, UserProfile


class TestPhysicianRegister(LiveServerTestCase):
    """
    Register physician test using an admin user.
    """
    @classmethod
    def setUpClass(cls):
        """
        Prepare environment before run the tests
        """
        super(TestPhysicianRegister, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        """
        Clean up the environment and db after all tests have finished.
        """
        super(TestPhysicianRegister, cls).tearDownClass()

    def test_register_physician(self):
        """
        Test register physician using an admin user.
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

            # Register physician
            register_user_by_admin(driver,
                                   first_name=TEMP_PHYSICIAN_USER['first_name'],
                                   last_name=TEMP_PHYSICIAN_USER['last_name'],
                                   username=TEMP_PHYSICIAN_USER['username'],
                                   email=TEMP_PHYSICIAN_USER['email'],
                                   role=TEMP_PHYSICIAN_USER['role'],
                                   password=TEMP_PHYSICIAN_USER['password'])

        finally:
            driver.quit()
