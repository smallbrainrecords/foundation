"""Test register for patient"""
from test.common import build_driver, login, register_patient, load_data, PATIENT_USER, TEMP_PATIENT_USER
from django.test import LiveServerTestCase


class TestPatientRegister(LiveServerTestCase):
    """
    Register test for patient users.
    """
    @classmethod
    def setUpClass(cls):
        """
        Prepare environment before run the tests
        """
        super(TestPatientRegister, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        """
        Clean up the environment and db after all tests have finished.
        """
        super(TestPatientRegister, cls).tearDownClass()

    def test_patient_register(self):
        """
        Test register patient.
        """
        try:
            # Prepare test
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
        finally:
            driver.quit()

    def test_patient_register_with_email_in_use(self):
        """
        Test register patient  with an email that is already in use by other patient.
        """
        try:
            # Prepare test
            load_data()
            driver = build_driver()

            # Register patient
            register_patient(driver,
                             base_url=self.live_server_url,
                             email=PATIENT_USER['email'],
                             password=PATIENT_USER['password'],
                             first_name=PATIENT_USER['first_name'],
                             last_name=PATIENT_USER['last_name'])

            assert driver.current_url == '{}/u/register/'.format(
                self.live_server_url, PATIENT_USER['email']), 'Register patient with email in use failed: user -> {}'.format(PATIENT_USER['email'])

            assert str(driver.find_element_by_xpath('//*[@id="dvmain"]/div/div[2]/div/div[2]/form/p[2]').text).startswith(
                'User with same email or username already exists'), 'Register patient with email in use failed: user -> {}'.format(PATIENT_USER['email'])
        finally:
            driver.quit()
