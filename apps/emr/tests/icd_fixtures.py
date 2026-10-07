"""A small, fixed ICD world for tests.

The real reference files change with every terminology release, so tests that
asserted against them would break twice a year for no reason. This mixin points
`emr.icd_codes` at four tiny files and loads a handful of map rows whose shapes
are the ones that matter:

  HTN         conditional row first, unconditional default second  -> I10
  CHOL        plain billable target                                 -> E78.00
  COUGH       plain billable target                                 -> R05.9
  DEPRESSION  billable target; the OLD table picked F32.9           -> F32.A
  SPRAIN      `?` seventh-character placeholder                     -> nothing
  FIT         no map row at all; the owner decided Z00.00
  DERM        no map row; the OLD table picked the billable L30.9
  RETIRED     no map row; its safe successor is COUGH
  UNKNOWN     no map row, no decision, no successor
"""
import json
import os
import shutil
import tempfile
from unittest import mock

from emr import icd_codes
from emr.models import SnomedIcd10Map

HTN = '38341003'
CHOL = '13644009'
COUGH = '49727002'
DEPRESSION = '35489007'
SPRAIN = '44465007'
FIT = '102499006'
DERM = '182782007'
RETIRED = '999000001'
UNKNOWN = '999000002'

BILLABLE = [
    'E78.00', 'F32.9', 'F32.A', 'I10', 'K21.9', 'L30.9', 'M54.50', 'R05.9',
    'R07.9', 'S93.401A', 'Z00.00',
]

MAP_ROWS = [
    # (concept, group, priority, code, advice)
    (HTN, 1, 1, 'P29.2', 'IF AGE AT ONSET OF CLINICAL FINDING BEFORE 29.0 DAYS CHOOSE P29.2'),
    (HTN, 1, 2, 'I10', 'ALWAYS I10'),
    (CHOL, 1, 1, 'E78.00', 'ALWAYS E78.00'),
    (COUGH, 1, 1, 'R05.9', 'ALWAYS R05.9'),
    (DEPRESSION, 1, 1, 'F32.A', 'ALWAYS F32.A'),
    (SPRAIN, 1, 1, 'S93.409?', 'ALWAYS S93.409? | EPISODE OF CARE INFORMATION NEEDED'),
]

MAP_HEADER = 'snomed_concept_id\tmap_group\tmap_priority\ticd10_code\tmap_advice\n'


def bundled_map_text(rows=MAP_ROWS):
    return (
        '# fixture map\n' + MAP_HEADER
        + ''.join(f'{c}\t{g}\t{p}\t{code}\t{advice}\n' for c, g, p, code, advice in rows)
    )


class IcdFixtureMixin:
    """Mix in before TestCase. Call `load_map_rows()` for the table itself."""

    def setUp(self):
        super().setUp()
        self.icd_dir = tempfile.mkdtemp(prefix='icd-fixture-')
        self.addCleanup(shutil.rmtree, self.icd_dir, True)

        self.billable_file = self._write('billable.txt', '# fixture\n' + '\n'.join(BILLABLE) + '\n')
        self.legacy_file = self._write(
            'legacy.tsv',
            '# fixture\nsnomed_concept_id\ticd10_code\n'
            f'{DEPRESSION}\tF32.9\n{DERM}\tL30.9\n',
        )
        self.decisions_file = self._write('decisions.json', json.dumps({
            'decisions': [{'concept': FIT, 'name': 'Fit and well (finding)', 'icd': 'Z00.00'}],
            'cancelled': [],
        }))
        self.map_file = self._write('map.tsv', bundled_map_text())

        for name, path in (
            ('BILLABLE_FILE', self.billable_file),
            ('LEGACY_FILE', self.legacy_file),
            ('DECISIONS_FILE', self.decisions_file),
            ('MAP_FILE', self.map_file),
        ):
            patcher = mock.patch.object(icd_codes, name, path)
            patcher.start()
            self.addCleanup(patcher.stop)

        # `emr.icd_map` took its own reference to MAP_FILE at import.
        from emr import icd_map
        patcher = mock.patch.object(icd_map, 'MAP_FILE', self.map_file)
        patcher.start()
        self.addCleanup(patcher.stop)

        retired = mock.patch(
            'emr.retired_concepts.SnomedRetiredConcept.replacement_for',
            side_effect=lambda concept: {RETIRED: COUGH}.get((concept or '').strip()),
        )
        retired.start()
        self.addCleanup(retired.stop)

        icd_codes.clear_caches()
        self.addCleanup(icd_codes.clear_caches)

    def _write(self, name, text):
        path = os.path.join(self.icd_dir, name)
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write(text)
        return path

    def write_decisions(self, decisions):
        with open(self.decisions_file, 'w', encoding='utf-8') as handle:
            json.dump({'decisions': [{'concept': c, 'icd': i} for c, i in decisions.items()]}, handle)
        icd_codes.clear_caches()

    def load_map_rows(self, rows=MAP_ROWS):
        SnomedIcd10Map.objects.all().delete()
        SnomedIcd10Map.objects.bulk_create([
            SnomedIcd10Map(snomed_concept_id=c, map_group=g, map_priority=p, icd10_code=code, map_advice=advice)
            for c, g, p, code, advice in rows
        ])
