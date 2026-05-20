import logging
import requests
import environ

from django.conf import settings

logger = logging.getLogger(__name__)
env = environ.Env()

class OpenEMRFHIRClient:
    """
    Client for communicating with OpenEMR's FHIR API.
    Expects to be running in the same GCP project or have network access to the OpenEMR FHIR base URL.
    """
    
    def __init__(self):
        # The base URL should look like https://my-openemr-host/apis/default/fhir
        self.base_url = env('OPENEMR_FHIR_BASE_URL', default='http://localhost/apis/default/fhir')
        self.access_token = env('OPENEMR_FHIR_ACCESS_TOKEN', default='')
        
        self.session = requests.Session()
        if self.access_token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/fhir+json',
                'Content-Type': 'application/fhir+json'
            })

    def get_patient(self, patient_id):
        url = f"{self.base_url}/Patient/{patient_id}"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch Patient={patient_id} from OpenEMR FHIR: {e}")
            return None

    def create_patient(self, given_name, family_name, gender, birth_date):
        url = f"{self.base_url}/Patient"
        payload = {
            "resourceType": "Patient",
            "name": [{
                "use": "official",
                "family": family_name,
                "given": [given_name]
            }],
            "gender": gender,
            "birthDate": birth_date
        }
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create Patient in OpenEMR FHIR: {e}")
            return None

    def sync_encounter(self, patient_fhir_id, status, encounter_class, start_time):
        url = f"{self.base_url}/Encounter"
        payload = {
            "resourceType": "Encounter",
            "status": status,  # e.g., 'finished'
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": encounter_class, # e.g., 'AMB' logic
            },
            "subject": {
                "reference": f"Patient/{patient_fhir_id}"
            },
            "period": {
                "start": start_time
            }
        }
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to sync Encounter to OpenEMR FHIR: {e}")
            return None
