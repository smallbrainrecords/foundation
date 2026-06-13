"""Import Document family. Phase 8. File binaries handled separately like audio."""
import json
import os
import tempfile
from datetime import datetime

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction, connection

from emr.models import Document, DocumentTodo, DocumentProblem, Problem, ToDo, Label

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
    def add_arguments(self, parser):
        parser.add_argument("--dump", type=str, required=True)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        dry = options["dry_run"]
        self.stdout.write(f"--- import_doc_family (dry_run={dry}) ---")

        dump = _load_json(options["dump"])
        l_docs = dump["documents"]
        l_dprobs = dump["doc_problems"]
        l_dtodos = dump["doc_todos"]
        self.stdout.write(f"dump: docs={len(l_docs)} doc_problems={len(l_dprobs)} doc_todos={len(l_dtodos)}")

        sbr1_doc_ids = set(Document.objects.filter(created_on__gte=CUTOFF).values_list("id", flat=True))
        self.stdout.write(f"sbr1_doc_ids to wipe: {len(sbr1_doc_ids)}")

        all_user_ids = set(User.objects.values_list("id", flat=True))
        existing_doc_ids = set(Document.objects.values_list("id", flat=True))

        if dry:
            self.stdout.write(self.style.SUCCESS("DRY RUN done."))
            return

        with transaction.atomic():
            # 1. Wipe SBR1 docs + existing-at-dump-id (idempotent).
            collide_ids = ({d["id"] for d in l_docs} & existing_doc_ids) - sbr1_doc_ids
            cleanup = sbr1_doc_ids | collide_ids
            del_docs = Document.objects.filter(id__in=cleanup).delete()
            self.stdout.write(f"wiped Documents (sum cascade): {del_docs[0]}")

            # 2. Wipe ALL DocumentProblem + DocumentTodo (replace from legacy).
            del_dp = DocumentProblem.objects.all().delete()
            del_dt = DocumentTodo.objects.all().delete()
            self.stdout.write(f"wiped DocumentProblem={del_dp[0]} DocumentTodo={del_dt[0]}")

            # 3. Insert Documents. created_on auto_now_add.
            doc_created = Document._meta.get_field("created_on")
            doc_created.auto_now_add = False
            try:
                new_docs = [
                    Document(
                        id=d["id"], document=d["document"] or "",
                        document_name=d["document_name"],
                        author_id=d["author_id"] if d["author_id"] in all_user_ids else None,
                        patient_id=d["patient_id"] if d["patient_id"] in all_user_ids else None,
                        created_on=_parse_dt(d["created_on"]),
                        client_uuid=d["client_uuid"],
                    )
                    for d in l_docs
                    if d["author_id"] in all_user_ids
                ]
                Document.objects.bulk_create(new_docs, batch_size=500)
            finally:
                doc_created.auto_now_add = True
            self.stdout.write(f"inserted Documents: {len(new_docs)}")

            # 4. Insert DocumentProblem + DocumentTodo — DROP IDs (auto-increment;
            #    join row IDs collide otherwise). FK filter on document/problem/todo.
            now_doc_ids = set(Document.objects.values_list("id", flat=True))
            now_prob_ids = set(Problem.objects.values_list("id", flat=True))
            now_todo_ids = set(ToDo.objects.values_list("id", flat=True))

            dprob_created = DocumentProblem._meta.get_field("created_on")
            dprob_created.auto_now_add = False
            try:
                new_dprobs = [
                    DocumentProblem(
                        document_id=r["document_id"], problem_id=r["problem_id"],
                        author_id=r["author_id"] if r["author_id"] in all_user_ids else None,
                        created_on=_parse_dt(r["created_on"]),
                    )
                    for r in l_dprobs
                    if r["document_id"] in now_doc_ids
                    and r["problem_id"] in now_prob_ids
                    and r["author_id"] in all_user_ids
                ]
                DocumentProblem.objects.bulk_create(new_dprobs, batch_size=500)
            finally:
                dprob_created.auto_now_add = True
            dp_skip = len(l_dprobs) - len(new_dprobs)
            self.stdout.write(f"inserted DocumentProblem: {len(new_dprobs)} (skipped {dp_skip})")

            dtodo_created = DocumentTodo._meta.get_field("created_on")
            dtodo_created.auto_now_add = False
            try:
                new_dtodos = [
                    DocumentTodo(
                        document_id=r["document_id"], todo_id=r["todo_id"],
                        author_id=r["author_id"] if r["author_id"] in all_user_ids else None,
                        created_on=_parse_dt(r["created_on"]),
                    )
                    for r in l_dtodos
                    if r["document_id"] in now_doc_ids
                    and r["todo_id"] in now_todo_ids
                    and r["author_id"] in all_user_ids
                ]
                DocumentTodo.objects.bulk_create(new_dtodos, batch_size=500)
            finally:
                dtodo_created.auto_now_add = True
            dt_skip = len(l_dtodos) - len(new_dtodos)
            self.stdout.write(f"inserted DocumentTodo: {len(new_dtodos)} (skipped {dt_skip})")

            # 5. Document.labels M2M (raw).
            doc_label_table = Document.labels.through._meta.db_table
            valid_label_ids = set(Label.objects.values_list("id", flat=True))
            m2m_rows = []
            for d in l_docs:
                if d["id"] not in now_doc_ids:
                    continue
                for lid in d.get("label_ids") or []:
                    if lid in valid_label_ids:
                        m2m_rows.append((d["id"], lid))
            if m2m_rows:
                with connection.cursor() as cur:
                    cur.execute(f"SELECT * FROM {doc_label_table} LIMIT 0")
                    cols = [c[0] for c in cur.description]
                    doc_col = next(c for c in cols if "document" in c.lower())
                    label_col = next(c for c in cols if "label" in c.lower())
                    sql = f"INSERT IGNORE INTO {doc_label_table} ({doc_col}, {label_col}) VALUES (%s, %s)"
                    cur.executemany(sql, m2m_rows)
            self.stdout.write(f"inserted Document.labels M2M: {len(m2m_rows)}")

        self.stdout.write(
            f"post-state: documents={Document.objects.count()} "
            f"DocumentProblem={DocumentProblem.objects.count()} "
            f"DocumentTodo={DocumentTodo.objects.count()}"
        )
        self.stdout.write(self.style.SUCCESS("Done. (Document file binaries deferred.)"))
