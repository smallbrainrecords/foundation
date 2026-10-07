"""What ICD-10 code a Problem may carry, and what to do with the one a client sent.

The rule this module exists to hold: **a problem's `icd10_code` is a billable
ICD-10-CM code or it is blank.** Never a category header (`E78.0`, `R05`), never
a WHO ICD-10 code (`R07.4`), never a `?` seventh-character placeholder
(`S93.409?`). These codes are printed on order requisitions and billed from.

Why it needed saying (2026-10-06): the map table had been loaded from SNOMED's
Full history file with the WHO map alongside the US one — see
`scripts/build_icd_data.py`. 7,830 of production's 24,272 coded problems (32%)
carried a code no lab could bill, and nothing anywhere checked.

Three bundled files back the rule, all built by `scripts/build_icd_data.py`:

  icd10cm_billable_codes.txt   the reference: every billable ICD-10-CM code
  icd10_legacy_map_picks.tsv   what the contaminated table picked, where that
                               was billable but not what the clean map assigns
  icd_concept_decisions.json   the owner's reviewed concept -> code decisions

Like `emr.retired_concepts` these are cached file reads, not models: static,
shipped in the image, small enough to hold in memory, and no migration.

**A missing reference file turns every check off rather than on.** If the
billable list cannot be read, `is_billable` answers True for everything, so the
endpoints behave exactly as they did before this module existed. The opposite
default — "nothing is billable" — would blank every code a client sends.
"""
import json
import logging
import os
from functools import lru_cache

logger = logging.getLogger(__name__)
_GUARD_LOGGER = logging.getLogger('smallbrain.icd_guard')

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
BILLABLE_FILE = os.path.join(DATA_DIR, 'icd10cm_billable_codes.txt')
LEGACY_FILE = os.path.join(DATA_DIR, 'icd10_legacy_map_picks.tsv')
DECISIONS_FILE = os.path.join(DATA_DIR, 'icd_concept_decisions.json')
MAP_FILE = os.path.join(DATA_DIR, 'snomed_icd10cm_map.tsv.gz')


def _data_lines(path):
    with open(path, encoding='utf-8') as handle:
        for line in handle:
            line = line.rstrip('\n')
            if line and not line.startswith('#'):
                yield line


@lru_cache(maxsize=1)
def billable_codes():
    """The billable ICD-10-CM codes, or None when the list cannot be read."""
    try:
        codes = frozenset(_data_lines(BILLABLE_FILE))
    except OSError:
        logger.warning('icd_codes: %s is missing; billable checks are off', BILLABLE_FILE)
        return None
    return codes or None


@lru_cache(maxsize=1)
def _legacy_picks():
    try:
        pairs = {}
        for line in _data_lines(LEGACY_FILE):
            concept, _, code = line.partition('\t')
            if concept and code and concept != 'snomed_concept_id':
                pairs[concept] = code
        return pairs
    except OSError:
        return {}


@lru_cache(maxsize=1)
def _decisions():
    try:
        with open(DECISIONS_FILE, encoding='utf-8') as handle:
            doc = json.load(handle)
    except (OSError, ValueError):
        return {}
    return {
        str(entry['concept']).strip(): str(entry['icd']).strip()
        for entry in doc.get('decisions', [])
        if entry.get('concept') and entry.get('icd')
    }


def clear_caches():
    """For tests that point the module at fixture files."""
    billable_codes.cache_clear()
    _legacy_picks.cache_clear()
    _decisions.cache_clear()


def normalize(code):
    return (code or '').strip().upper()


def is_billable(code):
    """True when `code` may be stored: a billable ICD-10-CM code.

    With no reference list loaded this answers True for any non-empty code —
    see the module docstring for why the checks fail open.
    """
    code = normalize(code)
    if not code:
        return False
    codes = billable_codes()
    return True if codes is None else code in codes


def _usable(code):
    """A map pick the server will hand out, or None.

    A `?` placeholder is never handed out (owner decision 2026-10-06): the map
    is saying "the seventh character depends on the visit" — initial,
    subsequent, sequela — and a problem outlives the visit, so any letter the
    server chose would be a guess on a billing document.
    """
    code = normalize(code)
    if not code or '?' in code or not is_billable(code):
        return None
    return code


def decision_for(concept_id):
    """The owner's reviewed code for a concept, if it is still billable."""
    return _usable(_decisions().get((concept_id or '').strip()))


def legacy_pick_for(concept_id):
    return _legacy_picks().get((concept_id or '').strip())


def explain_assignable(concept_id):
    """(code, source, concept) the server would assign to a concept.

    `source` is 'decision', 'map' or 'successor'; `concept` is the concept the
    code belongs to — the retired concept's active successor in the third
    case. (None, None, None) when nothing can be assigned.

    Order matters. The owner's decision wins over the map: every decision so
    far is for a concept the map cannot code, but a reviewed decision that
    disagrees with the map must also hold. Until 2026-10 decisions were applied
    once, by `apply_icd_decisions`, to the rows that existed that day — so every
    "Fit and well" problem created afterwards was blank.
    """
    from emr.models import SnomedIcd10Map
    from emr.retired_concepts import SnomedRetiredConcept

    concept = (concept_id or '').strip()
    if not concept:
        return None, None, None

    decided = decision_for(concept)
    if decided:
        return decided, 'decision', concept

    mapped = _usable(SnomedIcd10Map.best_icd10_for(concept))
    if mapped:
        return mapped, 'map', concept

    successor = SnomedRetiredConcept.replacement_for(concept)
    if successor and successor != concept:
        code = decision_for(successor) or _usable(SnomedIcd10Map.best_icd10_for(successor))
        if code:
            return code, 'successor', successor

    return None, None, None


def assignable_icd10_for(concept_id):
    """The billable code to stamp on a problem with this concept, or None.

    This — not `SnomedIcd10Map.best_icd10_for` — is what every assignment site
    calls. `best_icd10_for` is the raw map pick and can be a `?` placeholder.
    """
    return explain_assignable(concept_id)[0]


def placeholder_pick_for(concept_id):
    """The map's `?` pick for a concept (or its successor), else None.

    Lets the repair command tell "the map knows this concept but needs a
    seventh character" from "the map has nothing for it".
    """
    from emr.models import SnomedIcd10Map
    from emr.retired_concepts import SnomedRetiredConcept

    concept = (concept_id or '').strip()
    if not concept:
        return None
    for candidate in (concept, SnomedRetiredConcept.replacement_for(concept)):
        if not candidate:
            continue
        code = normalize(SnomedIcd10Map.best_icd10_for(candidate))
        if '?' in code:
            return code
    return None


def is_legacy_pick(concept_id, code):
    """True when `code` is what the contaminated table picked for this concept
    and the clean map assigns something else.

    Such a code is billable, so `is_billable` passes it, and it is still not a
    choice anybody made: it is an old app build's bundled map (or a client that
    has not pulled since the repair) echoing the old pick. When the clean map
    has nothing to offer instead, the old code is left alone — replacing a
    plausible code with a blank helps nobody.

    TEMPORARY. Once every Mac runs a build with the regenerated map, delete
    this function and its call: after that, the same code arriving from a
    client can only be a deliberate pick, and this would overrule it.
    """
    code = normalize(code)
    if not code or legacy_pick_for(concept_id) != code:
        return False
    assignable = assignable_icd10_for(concept_id)
    return bool(assignable) and assignable != code


def resolve_incoming_icd(concept_id, incoming, current='', concept_changed=False, context=None):
    """The `icd10_code` to store, given what the client sent.

    Used by problem create and update. The rules, in order:

    1. An incoming code that is billable and not a legacy pick is a real
       choice — a staged Common Problem code today, a manual picker tomorrow.
       It is stored as sent.
    2. Otherwise the incoming code says nothing (empty), or says something the
       server will not store. If the problem's concept just changed, the code
       the server holds belonged to the OLD concept, so assign for the new one,
       or blank. (Before this, an empty incoming code on a concept change left
       the old concept's code in place — a mismatched SNOMED/ICD pair.)
    3. Otherwise keep what the server holds, and assign only if it holds
       nothing. An empty or unusable incoming code never blanks a stored one:
       clients send `icd10Code ?? ""` on every problem update, so empty means
       "I have nothing", not "delete yours".

    `context` (a dict) is merged into the `smallbrain.icd_guard` log row written
    whenever a non-empty incoming code is not stored — that row is how to see
    which Macs are still stamping codes from an old bundled map.
    """
    concept = (concept_id or '').strip()
    incoming = normalize(incoming)
    current = (current or '').strip()

    reason = None
    if incoming:
        if not is_billable(incoming):
            reason = 'not_billable'
        elif is_legacy_pick(concept, incoming):
            reason = 'legacy_pick'
        else:
            return incoming

    if concept_changed or not current:
        stored = assignable_icd10_for(concept) or ''
    else:
        stored = current

    if reason:
        _GUARD_LOGGER.info(json.dumps({
            'event': 'client_code_replaced',
            'reason': reason,
            'concept_id': concept,
            'incoming': incoming,
            'stored': stored,
            **(context or {}),
        }))
    return stored
