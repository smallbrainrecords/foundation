"""Surgical import of legacy Problem family (Problem + ProblemNote +
ProblemRelationship + Problem.labels M2M) into smallbrain-db.

Phase 4 of the 2026-06-10 migration. Skips PatientImage binaries (paths
preserved, files copied separately like audio).
"""
import json
import os
import tempfile
from datetime import datetime

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction, connection

from emr.models import (
    Problem, ProblemNote, ProblemLabel, ProblemRelationship, PatientImage,
)

CUTOFF = "2026-04-25"


def _load_json(path):
    if path.startswith("gs://"):
        from google.cloud import storage as _gcs
        without_scheme = path[len("gs://"):]
        bucket_name, _, object_path = without_scheme.partition("/")
        tmp = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json", dir="/tmp")
        tmp.close()
        _gcs.Client().bucket(bucket_name).blob(object_path).download_to_filename(tmp.name)
        with open(tmp.name) as f:
            data = json.load(f)
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
        return data
    with open(path) as f:
        return json.load(f)


def _parse_dt(s):
    if s is None or s == "":
        return None
    return datetime.fromisoformat(s)


class Command(BaseCommand):
    help = "Import legacy Problem family. Idempotent."

    def add_arguments(self, parser):
        parser.add_argument("--dump", type=str, required=True)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        dry = options["dry_run"]
        self.stdout.write(f"--- import_problem_family (dry_run={dry}) ---")

        dump = _load_json(options["dump"])
        legacy_problems = dump["problems"]
        legacy_notes = dump["notes"]
        legacy_labels = dump["labels"]
        legacy_relationships = dump["relationships"]
        legacy_images = dump["images"]
        self.stdout.write(
            f"dump: problems={len(legacy_problems)} notes={len(legacy_notes)} "
            f"labels={len(legacy_labels)} relationships={len(legacy_relationships)} "
            f"images={len(legacy_images)}"
        )

        # SBR1-created problems in smallbrain = anything with start_date >= cutoff.
        sbr1_problem_ids = set(
            Problem.objects.filter(start_date__gte=CUTOFF).values_list("id", flat=True)
        )
        self.stdout.write(f"sbr1 problem ids to wipe: {len(sbr1_problem_ids)}")

        # Target = SBR1 ids (to replace) ∪ dump-only ids (legacy delta).
        dump_problem_ids = {p["id"] for p in legacy_problems}
        smallbrain_existing = set(
            Problem.objects.filter(id__in=dump_problem_ids).values_list("id", flat=True)
        )
        cleanup_ids = sbr1_problem_ids | smallbrain_existing
        self.stdout.write(
            f"cleanup_ids (wipe-before-insert): {len(cleanup_ids)}; "
            f"dump_ids: {len(dump_problem_ids)}"
        )

        # FK pre-filter: only insert problems whose patient_id (and parent_id if set) exists.
        all_user_ids = {p["patient_id"] for p in legacy_problems}
        existing_users = set(User.objects.filter(id__in=all_user_ids).values_list("id", flat=True))
        problems_keep = [p for p in legacy_problems if p["patient_id"] in existing_users]
        prob_skip = len(legacy_problems) - len(problems_keep)
        self.stdout.write(f"FK filter problems: keep={len(problems_keep)} skip={prob_skip}")

        # ProblemLabel — only insert labels not already in smallbrain.
        existing_label_ids = set(ProblemLabel.objects.values_list("id", flat=True))
        labels_keep = [l for l in legacy_labels if l["id"] not in existing_label_ids]
        self.stdout.write(f"new labels to insert: {len(labels_keep)}")

        if dry:
            self.stdout.write(self.style.SUCCESS("DRY RUN done."))
            return

        with transaction.atomic():
            # 1. Wipe cleanup_ids' rows. CASCADE handles ProblemNote, M2M label
            #    links, ProblemRelationship (FKs to source/target).
            #    EncounterProblemRecord also CASCADE — those for the SBR1
            #    problems will be deleted too (fine, they were also SBR1-only).
            del_problems = Problem.objects.filter(id__in=cleanup_ids).delete()
            self.stdout.write(f"deleted Problems (sum of cascade): {del_problems[0]}")

            # 2. Insert new ProblemLabels (rare).
            if labels_keep:
                new_labels = [
                    ProblemLabel(
                        id=l["id"], name=l["name"], css_class=l["css_class"],
                        author_id=l.get("author_id"), patient_id=l.get("patient_id"),
                    )
                    for l in labels_keep
                ]
                ProblemLabel.objects.bulk_create(new_labels)
                self.stdout.write(f"inserted ProblemLabels: {len(new_labels)}")

            # 3. Insert Problems. start_date + start_time are auto_now_add.
            start_date_field = Problem._meta.get_field("start_date")
            start_time_field = Problem._meta.get_field("start_time")
            start_date_field.auto_now_add = False
            start_time_field.auto_now_add = False
            try:
                new_probs = [
                    Problem(
                        id=p["id"], patient_id=p["patient_id"], parent_id=p["parent_id"],
                        problem_name=p["problem_name"], concept_id=p["concept_id"],
                        is_controlled=p["is_controlled"], is_active=p["is_active"],
                        authenticated=p["authenticated"],
                        start_date=_parse_dt(p["start_date"]),
                        old_problem_name=p["old_problem_name"],
                        lft=p["lft"], rght=p["rght"], tree_id=p["tree_id"], level=p["level"],
                    )
                    for p in problems_keep
                ]
                # Set start_time after construction (TimeField — string parse).
                from datetime import time as _time
                for prob_dict, prob in zip(problems_keep, new_probs):
                    st = prob_dict.get("start_time")
                    if st:
                        try:
                            h, m, *rest = st.split(":")
                            s = rest[0].split(".")[0] if rest else "0"
                            prob.start_time = _time(int(h), int(m), int(s))
                        except Exception:
                            prob.start_time = None
                # icd10_code may not exist on smallbrain — but it does per our PR-2.
                # Attempt set if dump has it.
                for prob_dict, prob in zip(problems_keep, new_probs):
                    if hasattr(prob, "icd10_code"):
                        prob.icd10_code = prob_dict.get("icd10_code")
                Problem.objects.bulk_create(new_probs, batch_size=500)
            finally:
                start_date_field.auto_now_add = True
                start_time_field.auto_now_add = True
            self.stdout.write(f"inserted Problems: {len(new_probs)}")

            # 4. Problem.labels M2M — repopulate using raw SQL for speed.
            problem_label_table = Problem.labels.through._meta.db_table
            m2m_rows = []
            inserted_prob_ids = {p["id"] for p in problems_keep}
            valid_label_ids = set(ProblemLabel.objects.values_list("id", flat=True))
            for p in problems_keep:
                if p["id"] not in inserted_prob_ids:
                    continue
                for lid in p["label_ids"]:
                    if lid in valid_label_ids:
                        m2m_rows.append((p["id"], lid))
            if m2m_rows:
                with connection.cursor() as cur:
                    # MySQL needs the exact column names. Inspect once.
                    cur.execute(f"SELECT * FROM {problem_label_table} LIMIT 0")
                    cols = [c[0] for c in cur.description]
                    prob_col = next(c for c in cols if "problem" in c.lower())
                    label_col = next(c for c in cols if "label" in c.lower())
                    sql = f"INSERT IGNORE INTO {problem_label_table} ({prob_col}, {label_col}) VALUES (%s, %s)"
                    cur.executemany(sql, m2m_rows)
            self.stdout.write(f"inserted Problem.labels M2M rows: {len(m2m_rows)}")

            # 5. ProblemNotes — only those whose problem exists in smallbrain post-import.
            existing_prob_ids = set(Problem.objects.values_list("id", flat=True))
            existing_user_ids = set(User.objects.values_list("id", flat=True))
            notes_keep = [
                n for n in legacy_notes
                if n["problem_id"] in existing_prob_ids
                and (n["author_id"] is None or n["author_id"] in existing_user_ids)
            ]
            note_skip = len(legacy_notes) - len(notes_keep)
            note_created_field = ProblemNote._meta.get_field("created_on")
            note_created_field.auto_now_add = False
            try:
                new_notes = [
                    ProblemNote(
                        id=n["id"], author_id=n["author_id"], problem_id=n["problem_id"],
                        note=n["note"], note_type=n["note_type"],
                        created_on=_parse_dt(n["created_on"]),
                    )
                    for n in notes_keep
                ]
                # Skip notes already in smallbrain at same id.
                existing_note_ids = set(ProblemNote.objects.filter(
                    id__in={n["id"] for n in notes_keep}
                ).values_list("id", flat=True))
                new_notes = [n for n in new_notes if n.id not in existing_note_ids]
                ProblemNote.objects.bulk_create(new_notes, batch_size=500)
            finally:
                note_created_field.auto_now_add = True
            self.stdout.write(f"inserted ProblemNotes: {len(new_notes)} (skip {note_skip} FK-orphans)")

            # 6. ProblemRelationships — only insert IDs not already there + FK check.
            existing_rel_ids = set(ProblemRelationship.objects.values_list("id", flat=True))
            rels_keep = [
                r for r in legacy_relationships
                if r["id"] not in existing_rel_ids
                and r["source_id"] in existing_prob_ids
                and r["target_id"] in existing_prob_ids
            ]
            new_rels = [
                ProblemRelationship(id=r["id"], source_id=r["source_id"], target_id=r["target_id"])
                for r in rels_keep
            ]
            ProblemRelationship.objects.bulk_create(new_rels, batch_size=500)
            self.stdout.write(f"inserted ProblemRelationships: {len(new_rels)}")

        # Post-state.
        self.stdout.write(
            f"post-state: problems={Problem.objects.count()} "
            f"notes={ProblemNote.objects.count()} "
            f"labels={ProblemLabel.objects.count()} "
            f"relationships={ProblemRelationship.objects.count()}"
        )
        self.stdout.write(self.style.SUCCESS("Done. (PatientImage binaries deferred to a separate file-recovery pass.)"))
