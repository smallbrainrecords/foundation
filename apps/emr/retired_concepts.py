"""Lookup for retired SNOMED concepts and their active successors.

Reads the same bundled file `remap_retired_concepts` uses
(`apps/emr/data/snomed_retired_concept_map.tsv`, 24,922 SAME_AS / REPLACED_BY
pairs from the licensed SNOMED CT US release), so the API guard and the data
heal can never disagree about what "retired" means.

Deliberately a cached file read rather than a model + migration: the data is
static, ships in the image, and is small enough to hold in memory (~25k pairs).
"""
import csv
import os
from functools import lru_cache

DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data",
    "snomed_retired_concept_map.tsv",
)


@lru_cache(maxsize=1)
def _retired_to_active():
    pairs = {}
    try:
        with open(DATA_FILE, encoding="utf-8") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                retired = (row.get("retired_concept_id") or "").strip()
                active = (row.get("active_concept_id") or "").strip()
                if retired and active:
                    pairs[retired] = active
    except OSError:
        # Missing file must degrade to "no concept is known-retired", which
        # makes the guard a no-op rather than blocking legitimate edits.
        return {}
    return pairs


class SnomedRetiredConcept:
    """Namespace for retired-concept questions the API needs to ask."""

    @staticmethod
    def replacement_for(concept_id):
        """The active successor for a retired concept, or None.

        None means "not a known-retired concept" — which includes both current
        concepts and anything outside the bundled map.
        """
        if not concept_id:
            return None
        return _retired_to_active().get(str(concept_id).strip())

    @staticmethod
    def is_retired(concept_id):
        return SnomedRetiredConcept.replacement_for(concept_id) is not None
