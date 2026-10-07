"""Reading the bundled SNOMED -> ICD-10-CM map file and comparing it to the table.

Kept apart from `emr.icd_codes` (the runtime rules) because only the two
management commands need it: `load_icd10_map` to replace the table, and
`repair_icd10_codes` to refuse to run against a table that is not the one the
image ships.
"""
import gzip
import zlib
from collections import Counter, defaultdict

from emr.icd_codes import MAP_FILE

HEADER = ['snomed_concept_id', 'map_group', 'map_priority', 'icd10_code', 'map_advice']


class MapFileError(Exception):
    pass


def read_bundled_map(path=None):
    """Rows (concept, group, priority, code, advice) from a file built by
    `scripts/build_icd_data.py`, plus its `#` header lines.

    Anything else is refused — in particular a raw SNOMED release file. The
    table was once filled straight from a release file, with no refset filter
    and from the Full history rather than the Snapshot, and a third of the
    codes it produced were not billable. The build script is the one place
    that knows how to read a release.
    """
    path = path or MAP_FILE
    opener = gzip.open if str(path).endswith('.gz') else open
    rows, comments, header_seen = [], [], False
    try:
        with opener(path, 'rt', encoding='utf-8', newline='') as handle:
            for line in handle:
                line = line.rstrip('\r\n')
                if not line:
                    continue
                if line.startswith('#'):
                    comments.append(line)
                    continue
                parts = line.split('\t')
                if not header_seen:
                    if parts != HEADER:
                        raise MapFileError(
                            f'{path}: not a bundled map file (header {parts[:5]}). '
                            'Build one with scripts/build_icd_data.py; raw SNOMED '
                            'release files are not accepted here.'
                        )
                    header_seen = True
                    continue
                if len(parts) != 5:
                    raise MapFileError(f'{path}: malformed row {line[:80]!r}')
                rows.append((parts[0], int(parts[1]), int(parts[2]), parts[3], parts[4]))
    except OSError as exc:
        raise MapFileError(f'{path}: {exc}')
    if not header_seen:
        raise MapFileError(f'{path}: empty file')
    return rows, comments


def fingerprint(keys):
    """(row count, checksum) over (concept, code, group, priority) tuples.

    Order-independent, so the file and the table can be compared without
    sorting either.
    """
    count, total = 0, 0
    for concept, code, group, priority in keys:
        count += 1
        total += zlib.crc32(f'{concept}#{code}#{group}#{priority}'.encode('utf-8'))
    return count, total


def file_fingerprint(rows):
    return fingerprint((c, code, g, p) for c, g, p, code, _ in rows)


def table_fingerprint(table=None):
    """The fingerprint of the map table (or of `table`, a staging copy).

    On MySQL the database computes it: `CRC32()` there is the same CRC-32 as
    `zlib.crc32`, and one aggregate row is far cheaper than streaming every map
    row to the job on production's small instance.
    """
    from django.db import connection
    from emr.models import SnomedIcd10Map

    table = table or SnomedIcd10Map._meta.db_table
    with connection.cursor() as cursor:
        name = connection.ops.quote_name(table)
        if connection.vendor == 'mysql':
            cursor.execute(
                "SELECT COUNT(*), COALESCE(SUM(CRC32(CONCAT_WS('#', snomed_concept_id, "
                f"icd10_code, map_group, map_priority))), 0) FROM {name}"
            )
            count, total = cursor.fetchone()
            return int(count), int(total)
        cursor.execute(f'SELECT snomed_concept_id, icd10_code, map_group, map_priority FROM {name}')
        return fingerprint(iter(cursor.fetchone, None))


def table_matches_bundled_map(path=None):
    rows, _ = read_bundled_map(path)
    return table_fingerprint() == file_fingerprint(rows)


def pick_report(rows, billable):
    """What `SnomedIcd10Map.best_icd10_for` would return for every concept in
    `rows`, summarised: counts by kind, the concepts whose winning rank is
    tied, and any duplicate keys.

    A tie means two rows share the best (conditional, group, priority), so the
    pick falls to the `id` tiebreak — to load order. A clean ICD-10-CM
    snapshot has none; the contaminated table had them wherever the WHO map
    and the US map both offered a first-priority row.
    """
    by_concept = defaultdict(list)
    keys = Counter()
    for concept, group, priority, code, advice in rows:
        by_concept[concept].append((1 if advice.startswith('IF ') else 0, group, priority, code))
        keys[(concept, code, group, priority)] += 1

    kinds, tied = Counter(), []
    for concept, candidates in by_concept.items():
        candidates.sort(key=lambda r: r[:3])
        if len(candidates) > 1 and candidates[0][:3] == candidates[1][:3]:
            tied.append(concept)
        code = candidates[0][3]
        if '?' in code:
            kinds['placeholder'] += 1
        elif billable is None:
            kinds['unchecked'] += 1
        elif code in billable:
            kinds['billable'] += 1
        else:
            kinds['other'] += 1

    duplicates = [key for key, n in keys.items() if n > 1]
    return {
        'concepts': len(by_concept),
        'kinds': dict(kinds),
        'tied': tied,
        'duplicates': duplicates,
    }
