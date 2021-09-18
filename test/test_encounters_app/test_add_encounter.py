"""Test create an encounter on a patient account"""
from test.common import build_driver, login, load_data, add_encounter, ADMIN_USER, manage_patient, PATIENT_USER, get_encounter_audio_route_DB, PHYSICIAN_ID, PATIENT_ID, delete_audio_from_media, delete_test_patient_media_folder
from django.test import LiveServerTestCase
from emr.models import User, UserProfile
import os

class TestAddEncounter(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        """
        Prepare environment before run the tests
        """
        super(TestAddEncounter, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        """
        Clean up the environment and db after all tests have finished.
        """
        super(TestAddEncounter, cls).tearDownClass()

    def test_add_encounter(self):
        """
        Test creating an encounter from a petient
        """
        try:
            # Get working directory
            cwd = os.getcwd()
            
            # Prepare test
            load_data()
            driver = build_driver()
            
            # Login as admin
            login(driver, 
                base_url=self.live_server_url, 
                username=ADMIN_USER['username'], 
                password=ADMIN_USER['password'])

            # Check if login worked 
            assert driver.current_url == '{}/project/{}/#/'.format(
                self.live_server_url, ADMIN_USER['username']), 'Login failed: user -> {}, {}'.format(ADMIN_USER['username'], ADMIN_USER['password'])
            
            # Manage patient
            manage_patient(driver, PATIENT_USER['username'])
            assert str(driver.current_url).startswith('{}/u/patient/manage/'.format(
                self.live_server_url)), 'Manage patient failed: patient -> {}'.format(PATIENT_USER['username'])
 
            # Add encounter
            add_encounter(driver,self.live_server_url)
            assert str(driver.current_url).startswith('{}/u/patient/manage/2/#/encounter/1'.format(
                self.live_server_url)), 'Failed to add encounter: patient -> {}'.format(PATIENT_USER['username'])

            # Clean up media folder
            audio_route = get_encounter_audio_route_DB(PHYSICIAN_ID,PATIENT_ID)
            delete_audio_from_media(cwd,audio_route)
            delete_test_patient_media_folder(cwd,audio_route)


        finally:
            driver.quit()
