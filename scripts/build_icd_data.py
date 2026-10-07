#!/usr/bin/env python3
"""Build the bundled ICD-10 data files in apps/emr/data/ from the licensed releases.

Three files, each with a `#` header naming its source:

  snomed_icd10cm_map.tsv.gz    the SNOMED CT -> ICD-10-CM map, loaded into
                               `SnomedIcd10Map` by `manage.py load_icd10_map`
  icd10cm_billable_codes.txt   every billable ICD-10-CM code, read by
                               `emr.icd_codes` to refuse non-billable codes
  icd10_legacy_map_picks.tsv   what the contaminated pre-2026-10 table picked
                               (only with --legacy-table-export; see below)

Why this script exists — the 2026-10-06 incident. The map table had been loaded
from the release's **Full** file with no refset filter. That put two things in
it that must never be there:

  * the WHO ICD-10 map (refset 447562003) next to the US ICD-10-CM map
    (refset 6011000124106). WHO codes look like ICD-10-CM and mostly are not
    billable: R05 for cough, M54.5 for low back pain, R07.4 for chest pain;
  * every superseded and inactivated version of every map entry. A Full file
    is a history; only the Snapshot says what is true now.

One coded problem in three carried a code no lab could bill. So this script
takes the **Snapshot** only, keeps the ICD-10-CM refset only, and refuses a
file in which any member id repeats — which is what a Full file looks like.

Run from the repo root, once per SNOMED US release (March, September) and once
per ICD-10-CM code set (October):

    python3 scripts/build_icd_data.py \\
        --snomed /path/to/SnomedCT_ManagedServiceUS_PRODUCTION_US1000124_<date> \\
        --icd    /path/to/icd10cm-order-<release>.txt

    python3 scripts/build_icd_data.py ... --check     # report, write nothing

`--legacy-table-export` takes a TSV export of the old table (id, concept, code,
group, priority, advice) and writes the legacy-picks file. That file can only
ever be built from an export taken BEFORE the table was reloaded; the export
used on 2026-10-06 is kept outside the repo and the result is committed.
"""
import argparse
import csv
import gzip
import io
import os
import sys
from collections import Counter, defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO, "apps", "emr", "data")

ICD10CM_REFSET = "6011000124106"
WHO_REFSET = "447562003"

MAP_OUT = os.path.join(DATA_DIR, "snomed_icd10cm_map.tsv.gz")
BILLABLE_OUT = os.path.join(DATA_DIR, "icd10cm_billable_codes.txt")
LEGACY_OUT = os.path.join(DATA_DIR, "icd10_legacy_map_picks.tsv")


def fail(message):
    sys.stderr.write("build_icd_data: " + message + "\n")
    sys.exit(1)


def dotted(code):
    """The CMS order file prints codes without the dot (E7800); we store E78.00."""
    return code if len(code) <= 3 else code[:3] + "." + code[3:]


def read_billable(order_file):
    """Billable codes from a CMS `icd10cm-order` file.

    Fixed width: the code is columns 7-13, the billable flag column 15 (1 =
    valid for submission, 0 = a category header that needs more characters).
    """
    billable, headers = set(), 0
    with open(order_file, encoding="utf-8", newline="") as handle:
        for line in handle:
            if len(line) < 16:
                continue
            code = line[6:13].strip()
            if not code:
                continue
            if line[14] == "1":
                billable.add(dotted(code))
            else:
                headers += 1
    if len(billable) < 50000:
        fail(f"{order_file}: only {len(billable)} billable codes — not an icd10cm-order file?")
    return billable, headers


def find_snapshot_map(snomed_dir):
    folder = os.path.join(snomed_dir, "Snapshot", "Refset", "Map")
    if os.path.isfile(snomed_dir):
        return snomed_dir
    if not os.path.isdir(folder):
        fail(f"no Snapshot/Refset/Map under {snomed_dir}")
    names = [n for n in os.listdir(folder) if "ExtendedMapSnapshot" in n and n.endswith(".txt")]
    if len(names) != 1:
        fail(f"expected one ExtendedMapSnapshot file in {folder}, found {names}")
    return os.path.join(folder, names[0])


def read_icd10cm_rows(map_file):
    """(concept, group, priority, code, advice) for the active ICD-10-CM rows.

    RF2 columns: 0 id, 1 effectiveTime, 2 active, 3 moduleId, 4 refsetId,
    5 referencedComponentId, 6 mapGroup, 7 mapPriority, 8 mapRule,
    9 mapAdvice, 10 mapTarget.
    """
    rows, seen_ids, by_refset = [], set(), Counter()
    with open(map_file, encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t", quoting=csv.QUOTE_NONE)
        header = next(reader)
        if header[:5] != ["id", "effectiveTime", "active", "moduleId", "refsetId"]:
            fail(f"{map_file}: not an RF2 extended-map file (header {header[:5]})")
        for row in reader:
            member = row[0]
            if member in seen_ids:
                fail(
                    f"{map_file}: member id {member} appears more than once. "
                    "That is a Full (history) file — use the Snapshot."
                )
            seen_ids.add(member)
            by_refset[row[4]] += 1
            if row[4] != ICD10CM_REFSET or row[2] != "1":
                continue
            target = row[10].strip()
            if not target:
                continue
            rows.append((row[5], int(row[6]), int(row[7]), target, row[9]))
    if not rows:
        fail(f"{map_file}: no active rows for refset {ICD10CM_REFSET}")
    return rows, by_refset


def pick(rows):
    """Django's `SnomedIcd10Map.best_icd10_for`, minus the `id` tiebreak.

    Returns (code, tied): tied is True when two rows share the winning
    (conditional, group, priority) rank, which would make the pick depend on
    load order. A clean ICD-10-CM snapshot has none.
    """
    ranked = sorted(rows, key=lambda r: (1 if r[4].startswith("IF ") else 0, r[1], r[2]))
    first = ranked[0]
    tied = len(ranked) > 1 and (
        (first[4].startswith("IF "), first[1], first[2])
        == (ranked[1][4].startswith("IF "), ranked[1][1], ranked[1][2])
    )
    return first[3], tied


def write_gz(path, text):
    buffer = io.BytesIO()
    # mtime=0 keeps the bytes identical between runs on the same input.
    with gzip.GzipFile(fileobj=buffer, mode="wb", compresslevel=9, mtime=0) as gz:
        gz.write(text.encode("utf-8"))
    with open(path, "wb") as handle:
        handle.write(buffer.getvalue())


def read_legacy_export(path):
    """concept -> the code the old table picked (conditional, group, priority, id)."""
    opener = gzip.open if path.endswith(".gz") else open
    best = {}
    with opener(path, "rt", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t", quoting=csv.QUOTE_NONE)
        header = next(reader)
        if header[:3] != ["id", "snomed_concept_id", "icd10_code"]:
            fail(f"{path}: not a table export (header {header[:3]})")
        for row in reader:
            advice = row[5] if len(row) > 5 else ""
            key = (1 if advice.startswith("IF ") else 0, int(row[3]), int(row[4]), int(row[0]))
            current = best.get(row[1])
            if current is None or key < current[0]:
                best[row[1]] = (key, row[2])
    return {concept: code for concept, (_, code) in best.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--snomed", required=True, help="SNOMED US Edition release folder (or the Snapshot map file)")
    parser.add_argument("--icd", required=True, help="CMS icd10cm-order file")
    parser.add_argument("--legacy-table-export", help="TSV export of the pre-fix table; writes the legacy-picks file")
    parser.add_argument("--check", action="store_true", help="report only, write nothing")
    args = parser.parse_args()

    billable, headers = read_billable(args.icd)
    map_file = find_snapshot_map(args.snomed)
    rows, by_refset = read_icd10cm_rows(map_file)

    by_concept = defaultdict(list)
    for row in rows:
        by_concept[row[0]].append(row)

    picks, tied = {}, []
    for concept, concept_rows in by_concept.items():
        code, is_tied = pick(concept_rows)
        picks[concept] = code
        if is_tied:
            tied.append(concept)

    kinds = Counter(
        "billable" if code in billable else "placeholder" if "?" in code else "other"
        for code in picks.values()
    )
    print(f"ICD-10-CM order file : {os.path.basename(args.icd)}")
    print(f"  billable codes     : {len(billable)}   (category headers: {headers})")
    print(f"SNOMED map file      : {os.path.basename(map_file)}")
    print(f"  rows by refset     : {dict(by_refset)}")
    print(f"  ICD-10-CM rows kept: {len(rows)}  ({len(by_concept)} concepts)")
    print(f"  picks              : {dict(kinds)}")
    print(f"  tied top ranks     : {len(tied)}")

    if tied:
        fail(f"{len(tied)} concepts have a tied top rank (e.g. {tied[:5]}); the pick would depend on load order")
    if kinds["other"] > 0.01 * len(picks):
        fail(
            f"{kinds['other']} picks are neither billable nor a ? placeholder. "
            "The map and the code list are from mismatched releases, or the wrong refset was read."
        )

    map_name, icd_name = os.path.basename(map_file), os.path.basename(args.icd)
    ordered = sorted(rows, key=lambda r: (r[0], r[1], r[2], r[3]))
    map_text = (
        f"# SNOMED CT -> ICD-10-CM map. Source: {map_name}\n"
        f"# Snapshot, refset {ICD10CM_REFSET} only, active rows with a target. {len(rows)} rows.\n"
        "# Built by scripts/build_icd_data.py — do not edit by hand.\n"
        "snomed_concept_id\tmap_group\tmap_priority\ticd10_code\tmap_advice\n"
        + "".join(f"{c}\t{g}\t{p}\t{code}\t{advice}\n" for c, g, p, code, advice in ordered)
    )
    billable_text = (
        f"# Billable ICD-10-CM codes. Source: {icd_name}\n"
        f"# {len(billable)} codes; category headers are deliberately absent.\n"
        "# Built by scripts/build_icd_data.py — do not edit by hand.\n"
        + "".join(code + "\n" for code in sorted(billable))
    )

    legacy_text = None
    if args.legacy_table_export:
        old = read_legacy_export(args.legacy_table_export)

        def assignable(concept):
            code = picks.get(concept)
            return code if code and code in billable else None

        legacy = sorted(
            (concept, code) for concept, code in old.items()
            if code in billable and assignable(concept) != code
        )
        print(f"legacy table export  : {os.path.basename(args.legacy_table_export)}")
        print(f"  concepts in export : {len(old)}")
        print(f"  legacy picks kept  : {len(legacy)}  (billable, and not what the clean map assigns)")
        legacy_text = (
            "# What the contaminated pre-2026-10 map table picked, where that pick is a billable\n"
            "# code and differs from what the clean ICD-10-CM map assigns. Read by emr.icd_codes\n"
            "# to recognise a code stamped by an old app build or the old server pick.\n"
            f"# Old table: {os.path.basename(args.legacy_table_export)}; clean map: {map_name}.\n"
            "# Cannot be rebuilt once the export is gone. Do not edit by hand.\n"
            "snomed_concept_id\ticd10_code\n"
            + "".join(f"{concept}\t{code}\n" for concept, code in legacy)
        )

    if args.check:
        print("--check: nothing written")
        return 0

    os.makedirs(DATA_DIR, exist_ok=True)
    write_gz(MAP_OUT, map_text)
    with open(BILLABLE_OUT, "w", encoding="utf-8") as handle:
        handle.write(billable_text)
    print(f"wrote {os.path.relpath(MAP_OUT, REPO)} ({os.path.getsize(MAP_OUT) / 1e6:.2f} MB)")
    print(f"wrote {os.path.relpath(BILLABLE_OUT, REPO)} ({os.path.getsize(BILLABLE_OUT) / 1e3:.0f} KB)")
    if legacy_text is not None:
        with open(LEGACY_OUT, "w", encoding="utf-8") as handle:
            handle.write(legacy_text)
        print(f"wrote {os.path.relpath(LEGACY_OUT, REPO)} ({os.path.getsize(LEGACY_OUT) / 1e3:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
