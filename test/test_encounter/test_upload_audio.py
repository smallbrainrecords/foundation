"""Test on patient account"""
from test.common import build_driver, login, load_data, ADMIN_USER, manage_patient, PATIENT_USER, upload_audio, PHYSICIAN_ID, PATIENT_ID, get_encounter_audio_route_DB, delete_audio_from_media, assert_audio_encounter, delete_test_patient_media_folder, assert_audio_conversion
from django.test import LiveServerTestCase
from emr.models import User, UserProfile
import os

class TestUploadAudio(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        """
        Prepare environment before run the tests
        """
        super(TestUploadAudio, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        """
        Clean up the environment and db after all tests have finished.
        """
        super(TestUploadAudio, cls).tearDownClass()

    def test_upload_audio(self):
        """
        Test upload an audio for a patient
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

            # Upload audio
            upload_audio(driver,cwd)
            assert str(driver.current_url).startswith('{}/u/patient/manage/2/#/encounter/1'.format(
                self.live_server_url)), 'Failed to add encounter with audio: patient -> {}'.format(PATIENT_USER['username'])
            
            # Assert audio encounter
            audio_route = get_encounter_audio_route_DB(PHYSICIAN_ID,PATIENT_ID)
            assert assert_audio_encounter(cwd,audio_route)

            # Assert audio encounter
            assert assert_audio_conversion(cwd,audio_route)   
            
            # Clean up media folder
            delete_audio_from_media(cwd,audio_route)
            delete_test_patient_media_folder(cwd,audio_route)
   
        finally:
            driver.quit()