"""Surgical import of legacy Todo family into smallbrain-db. Phase 5.
Wipes SBR1-created todos (created_on >= cutoff) + all TaggedToDoOrder rows
(small table, fully replaceable), then inserts legacy delta + comments + labels.
"""
import json
import os
import tempfile
from datetime import datetime

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction, connection

from emr.models import ToDo, TaggedToDoOrder, ToDoComment, Label

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
    help = "Import legacy Todo family. Idempotent."

    def add_arguments(self, parser):
        parser.add_argument("--dump", type=str, required=True)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        dry = options["dry_run"]
        self.stdout.write(f"--- import_todo_family (dry_run={dry}) ---")

        dump = _load_json(options["dump"])
        legacy_todos = dump["todos"]
        legacy_labels = dump["labels"]
        legacy_tagged = dump["tagged"]
        legacy_comments = dump["comments"]
        self.stdout.write(
            f"dump: todos={len(legacy_todos)} labels={len(legacy_labels)} "
            f"tagged={len(legacy_tagged)} comments={len(legacy_comments)}"
        )

        # SBR1 todos in smallbrain
        sbr1_todo_ids = set(
            ToDo.objects.filter(created_on__gte=CUTOFF).values_list("id", flat=True)
        )
        dump_todo_ids = {t["id"] for t in legacy_todos}
        cleanup_todo_ids = sbr1_todo_ids | (
            set(ToDo.objects.filter(id__in=dump_todo_ids).values_list("id", flat=True))
        )
        self.stdout.write(f"sbr1_todo_ids={len(sbr1_todo_ids)}, cleanup_todo_ids={len(cleanup_todo_ids)}")

        # FK filter
        all_user_ids = {t["user_id"] for t in legacy_todos if t["user_id"]} | {t["patient_id"] for t in legacy_todos if t["patient_id"]}
        existing_users = set(User.objects.filter(id__in=all_user_ids).values_list("id", flat=True))
        # Problem FKs — only those that exist (SET_NULL on missing is the legacy default
        # so unmatched problem_ids drop to NULL on insert).
        from emr.models import Problem
        prob_ids_needed = {t["problem_id"] for t in legacy_todos if t["problem_id"]}
        existing_probs = set(Problem.objects.filter(id__in=prob_ids_needed).values_list("id", flat=True))

        todos_keep = [
            t for t in legacy_todos
            if (t["user_id"] is None or t["user_id"] in existing_users)
            and (t["patient_id"] is None or t["patient_id"] in existing_users)
        ]
        todo_skip = len(legacy_todos) - len(todos_keep)
        self.stdout.write(f"FK filter todos: keep={len(todos_keep)} skip={todo_skip}")

        if dry:
            self.stdout.write(self.style.SUCCESS("DRY RUN done."))
            return

        with transaction.atomic():
            # 1. Wipe TaggedToDoOrder entirely (small, no user content; replace from legacy).
            del_tagged = TaggedToDoOrder.objects.all().delete()
            self.stdout.write(f"wiped TaggedToDoOrder: {del_tagged[0]}")

            # 2. Wipe target todos (SBR1 + already-present at dump IDs). CASCADE
            #    handles ToDoComment, labels M2M, and notes M2M.
            del_todos = ToDo.objects.filter(id__in=cleanup_todo_ids).delete()
            self.stdout.write(f"wiped Todos (cascade): {del_todos[0]}")

            # 3. Sync Labels — bulk_create new ones.
            existing_label_ids = set(Label.objects.values_list("id", flat=True))
            new_labels = [
                Label(id=l["id"], name=l["name"], css_class=l["css_class"],
                      author_id=l["author_id"] if l["author_id"] in existing_users else None,
                      is_all=l["is_all"])
                for l in legacy_labels if l["id"] not in existing_label_ids
            ]
            if new_labels:
                Label.objects.bulk_create(new_labels)
            self.stdout.write(f"inserted Labels: {len(new_labels)}")

            # 4. Insert Todos. created_on has auto_now_add — disable.
            created_field = ToDo._meta.get_field("created_on")
            created_field.auto_now_add = False
            try:
                new_todos = [
                    ToDo(
                        id=t["id"], todo=t["todo"], accomplished=t["accomplished"],
                        due_date=_parse_dt(t["due_date"]),
                        order=t["order"],
                        user_id=t["user_id"] if t["user_id"] in existing_users else None,
                        patient_id=t["patient_id"] if t["patient_id"] in existing_users else None,
                        problem_id=t["problem_id"] if t["problem_id"] in existing_probs else None,
                        created_at=t["created_at"],
                        created_on=_parse_dt(t["created_on"]),
                    )
                    for t in todos_keep
                ]
                ToDo.objects.bulk_create(new_todos, batch_size=500)
            finally:
                created_field.auto_now_add = True
            self.stdout.write(f"inserted Todos: {len(new_todos)}")

            # 5. Todo.labels M2M (raw SQL for speed).
            existing_label_ids2 = set(Label.objects.values_list("id", flat=True))
            todo_label_table = ToDo.labels.through._meta.db_table
            m2m_rows = []
            inserted_todo_ids = {t["id"] for t in todos_keep}
            for t in todos_keep:
                if t["id"] not in inserted_todo_ids:
                    continue
                for lid in t["label_ids"]:
                    if lid in existing_label_ids2:
                        m2m_rows.append((t["id"], lid))
            if m2m_rows:
                with connection.cursor() as cur:
                    cur.execute(f"SELECT * FROM {todo_label_table} LIMIT 0")
                    cols = [c[0] for c in cur.description]
                    todo_col = next(c for c in cols if "todo" in c.lower())
                    label_col = next(c for c in cols if "label" in c.lower())
                    sql = f"INSERT IGNORE INTO {todo_label_table} ({todo_col}, {label_col}) VALUES (%s, %s)"
                    cur.executemany(sql, m2m_rows)
            self.stdout.write(f"inserted Todo.labels M2M: {len(m2m_rows)}")

            # 6. TaggedToDoOrder — insert all from legacy, FK-filter.
            existing_todo_ids = set(ToDo.objects.values_list("id", flat=True))
            all_users_global = set(User.objects.values_list("id", flat=True))
            tagged_keep = [
                t for t in legacy_tagged
                if (t["todo_id"] is None or t["todo_id"] in existing_todo_ids)
                and (t["user_id"] is None or t["user_id"] in all_users_global)
            ]
            tagged_created_field = TaggedToDoOrder._meta.get_field("created_on")
            tagged_created_field.auto_now_add = False
            try:
                new_tagged = [
                    TaggedToDoOrder(
                        id=t["id"], order=t["order"], status=t["status"],
                        todo_id=t["todo_id"], user_id=t["user_id"],
                        created_on=_parse_dt(t["created_on"]),
                    )
                    for t in tagged_keep
                ]
                TaggedToDoOrder.objects.bulk_create(new_tagged, batch_size=500)
            finally:
                tagged_created_field.auto_now_add = True
            self.stdout.write(f"inserted TaggedToDoOrder: {len(new_tagged)}")

            # 7. ToDoComment — insert post-cutoff; FK-filter. datetime has auto_now (not auto_now_add)
            #    so it would fire on every save. Disable. existing_comment_ids
            #    MUST be recomputed AFTER the todo wipe (which cascades comments).
            existing_comment_ids = set(ToDoComment.objects.filter(
                id__in={c["id"] for c in legacy_comments}
            ).values_list("id", flat=True))
            comments_keep = [
                c for c in legacy_comments
                if c["id"] not in existing_comment_ids
                and c["todo_id"] in existing_todo_ids
                and c["user_id"] in all_users_global
            ]
            comment_dt_field = ToDoComment._meta.get_field("datetime")
            comment_dt_field.auto_now = False
            try:
                new_comments = [
                    ToDoComment(
                        id=c["id"], todo_id=c["todo_id"], user_id=c["user_id"],
                        comment=c["comment"], datetime=_parse_dt(c["datetime"]),
                    )
                    for c in comments_keep
                ]
                ToDoComment.objects.bulk_create(new_comments, batch_size=500)
            finally:
                comment_dt_field.auto_now = True
            self.stdout.write(f"inserted ToDoComments: {len(new_comments)}")

        # Post-state
        self.stdout.write(
            f"post-state: todos={ToDo.objects.count()} comments={ToDoComment.objects.count()} "
            f"tagged={TaggedToDoOrder.objects.count()} labels={Label.objects.count()}"
        )
        self.stdout.write(self.style.SUCCESS("Done."))
