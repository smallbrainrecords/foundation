"""
Test reject patient register
"""
from test.common import build_driver, login, register_patient, reject_user, load_data, ADMIN_USER, TEMP_PATIENT_USER, reject_user
from django.test import LiveServerTestCase


class TestRejectPatientRegister(LiveServerTestCase):
    """
    Reject patient register test using admin user.
    """
    @classmethod
    def setUpClass(cls):
        """
        Prepare environment before run the tests
        """
        super(TestRejectPatientRegister, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        """
        Clean up the environment and db after all tests have finished.
        """
        super(TestRejectPatientRegister, cls).tearDownClass()

    def test_reject_patient_register(self):
        """
        Test reject register patient using admin user.
        """
        try:
            # Prepare test (part 1)
            load_data()
            driver = build_driver()

            # Register patient
            register_patient(driver,
                             base_url=self.live_server_url,
                             email=TEMP_PATIENT_USER['email'],
                             password=TEMP_PATIENT_USER['password'],
                             first_name=TEMP_PATIENT_USER['first_name'],
                             last_name=TEMP_PATIENT_USER['last_name'])

            assert driver.current_url == '{}/u/home/'.format(
                self.live_server_url), 'Register patient failed: user -> {}'.format(TEMP_PATIENT_USER['email'])

            assert str(driver.find_element_by_xpath('/html/body/p').text).startswith(
                'Your account is created but your profile is not verified.')

            driver.quit()

            # Prepare test (part 2)
            driver = build_driver()

            # Login as admin
            login(driver,
                  base_url=self.live_server_url,
                  username=ADMIN_USER['username'],
                  password=ADMIN_USER['password'])

            # Check results
            assert driver.current_url == '{}/project/{}/#/'.format(
                self.live_server_url, ADMIN_USER['username']), 'Login failed: user -> {}, {}'.format(ADMIN_USER['username'], ADMIN_USER['password'])

            # Reject patient
            reject_user(
                driver, TEMP_PATIENT_USER['username'])
        
        finally:
            driver.quit()
