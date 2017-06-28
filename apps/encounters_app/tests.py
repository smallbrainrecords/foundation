from django.test import TestCase
from emr.models import Encounter

# Create your tests here.

class EncounterTestCase(TestCase):
    def setUp(self):
        Encounter.objects.create()

    def test_toggle_encounter_recorder_status(self):
        """

        :return:
        """
        self.assertEqual()