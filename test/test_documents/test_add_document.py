"""Test on patient account"""
from test.common import build_driver, login, load_data, ADMIN_USER, manage_patient, PATIENT_USER, PHYSICIAN_ID, PATIENT_ID, add_document, assert_add_document, delete_document_from_media, delete_document_media_folder
from django.test import LiveServerTestCase
from emr.models import User, UserProfile
import os
from time import sleep

class TestAddDocument(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        """
        Prepare environment before run the tests
        """
        super(TestAddDocument, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        """
        Clean up the environment and db after all tests have finished.
        """
        super(TestAddDocument, cls).tearDownClass()

    def test_add_document(self):
        """
        Test add a document for a patient
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

            # Add document
            add_document(driver,cwd)
            
            # Assert add document
            assert assert_add_document(cwd)
            
            # Clean up media folder
            delete_document_from_media (cwd)
            delete_document_media_folder(cwd)
 
   
        finally:
            driver.quit()