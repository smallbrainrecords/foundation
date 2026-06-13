"""Import CommonProblems + post-cutoff ProblemActivity + TodoActivity. Phases 9 + 10."""
import json
import os
import tempfile
from datetime import datetime

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from emr.models import (
    CommonProblem, ProblemActivity, TodoActivity, Problem, ToDo, ToDoComment,
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
    def add_arguments(self, parser):
        parser.add_argument("--dump", type=str, required=True)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        dry = options["dry_run"]
        self.stdout.write(f"--- import_misc_family (dry_run={dry}) ---")
        dump = _load_json(options["dump"])
        commons = dump["commons"]
        prob_acts = dump["prob_acts"]
        todo_acts = dump["todo_acts"]
        self.stdout.write(f"dump: commons={len(commons)} prob_acts={len(prob_acts)} todo_acts={len(todo_acts)}")

        all_user_ids = set(User.objects.values_list("id", flat=True))

        if dry:
            self.stdout.write(self.style.SUCCESS("DRY RUN done."))
            return

        with transaction.atomic():
            # CommonProblem — wipe and replace (small, no user content).
            CommonProblem.objects.all().delete()
            new_cps = [
                CommonProblem(
                    id=c["id"], problem_name=c["problem_name"],
                    concept_id=c["concept_id"], problem_type=c["problem_type"],
                    author_id=c["author_id"] if c["author_id"] in all_user_ids else None,
                )
                for c in commons
            ]
            CommonProblem.objects.bulk_create(new_cps)
            self.stdout.write(f"inserted CommonProblems: {len(new_cps)}")

            # ProblemActivity — wipe post-cutoff + insert from dump.
            sbr1_pa = ProblemActivity.objects.filter(created_on__gte=CUTOFF)
            del_pa = sbr1_pa.delete()
            self.stdout.write(f"wiped post-cutoff ProblemActivity: {del_pa[0]}")

            now_prob_ids = set(Problem.objects.values_list("id", flat=True))
            pa_created = ProblemActivity._meta.get_field("created_on")
            pa_created.auto_now_add = False
            try:
                new_pas = [
                    ProblemActivity(
                        id=a["id"],
                        problem_id=a["problem_id"] if (a["problem_id"] is None or a["problem_id"] in now_prob_ids) else None,
                        author_id=a["author_id"] if a["author_id"] in all_user_ids else None,
                        activity=a["activity"],
                        is_input_type=a["is_input_type"], is_output_type=a["is_output_type"],
                        created_on=_parse_dt(a["created_on"]),
                    )
                    for a in prob_acts
                ]
                ProblemActivity.objects.bulk_create(new_pas, batch_size=500)
            finally:
                pa_created.auto_now_add = True
            self.stdout.write(f"inserted ProblemActivity: {len(new_pas)}")

            # TodoActivity — wipe post-cutoff + insert from dump.
            sbr1_ta = TodoActivity.objects.filter(created_on__gte=CUTOFF)
            del_ta = sbr1_ta.delete()
            self.stdout.write(f"wiped post-cutoff TodoActivity: {del_ta[0]}")

            now_todo_ids = set(ToDo.objects.values_list("id", flat=True))
            now_comment_ids = set(ToDoComment.objects.values_list("id", flat=True))
            ta_created = TodoActivity._meta.get_field("created_on")
            ta_created.auto_now_add = False
            try:
                new_tas = [
                    TodoActivity(
                        id=a["id"],
                        todo_id=a["todo_id"],
                        author_id=a["author_id"] if a["author_id"] in all_user_ids else None,
                        comment_id=a["comment_id"] if (a["comment_id"] is None or a["comment_id"] in now_comment_ids) else None,
                        attachment_id=None,  # ToDoAttachment is skip-listed.
                        activity=a["activity"],
                        created_on=_parse_dt(a["created_on"]),
                    )
                    for a in todo_acts
                    if a["todo_id"] in now_todo_ids
                ]
                TodoActivity.objects.bulk_create(new_tas, batch_size=500)
            finally:
                ta_created.auto_now_add = True
            ta_skip = len(todo_acts) - len(new_tas)
            self.stdout.write(f"inserted TodoActivity: {len(new_tas)} (skipped {ta_skip} FK-orphans)")

        self.stdout.write(
            f"post-state: CommonProblem={CommonProblem.objects.count()} "
            f"ProblemActivity={ProblemActivity.objects.count()} "
            f"TodoActivity={TodoActivity.objects.count()}"
        )
        self.stdout.write(self.style.SUCCESS("Done."))
