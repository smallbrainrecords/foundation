"""Wipe-and-replace PhysicianTeam + PatientController from legacy dump.
No user content in these tables — safe to wipe + replace. FK-filter rows
that reference users not yet migrated."""
import json
import os
import tempfile

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from emr.models import PhysicianTeam, PatientController


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


class Command(BaseCommand):
    help = "Wipe-and-replace PhysicianTeam + PatientController from legacy dump."

    def add_arguments(self, parser):
        parser.add_argument("--dump", type=str, required=True)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        dry = options["dry_run"]
        self.stdout.write(f"--- import_team_tables (dry_run={dry}) ---")

        dump = _load_json(options["dump"])
        teams = dump["physician_teams"]
        controllers = dump["patient_controllers"]
        self.stdout.write(f"dump: teams={len(teams)} controllers={len(controllers)}")

        # FK filter — only insert rows whose referenced user IDs exist.
        all_user_ids = set()
        for t in teams:
            all_user_ids.add(t["physician_id"])
            all_user_ids.add(t["member_id"])
        for c in controllers:
            all_user_ids.add(c["patient_id"])
            all_user_ids.add(c["physician_id"])
        existing_users = set(User.objects.filter(id__in=all_user_ids).values_list("id", flat=True))

        teams_keep = [t for t in teams if t["physician_id"] in existing_users and t["member_id"] in existing_users]
        controllers_keep = [c for c in controllers if c["patient_id"] in existing_users and c["physician_id"] in existing_users]
        teams_skip = len(teams) - len(teams_keep)
        ctrl_skip = len(controllers) - len(controllers_keep)
        self.stdout.write(f"FK filter: teams_keep={len(teams_keep)} (skip {teams_skip}), controllers_keep={len(controllers_keep)} (skip {ctrl_skip})")

        # Pre-state.
        self.stdout.write(f"smallbrain pre-state: teams={PhysicianTeam.objects.count()} controllers={PatientController.objects.count()}")

        if dry:
            self.stdout.write(self.style.SUCCESS("DRY RUN done."))
            return

        with transaction.atomic():
            del_teams = PhysicianTeam.objects.all().delete()
            del_ctrl = PatientController.objects.all().delete()
            self.stdout.write(f"deleted: teams={del_teams[0]} controllers={del_ctrl[0]}")

            new_teams = [
                PhysicianTeam(id=t["id"], physician_id=t["physician_id"], member_id=t["member_id"])
                for t in teams_keep
            ]
            PhysicianTeam.objects.bulk_create(new_teams)
            self.stdout.write(f"inserted teams: {len(new_teams)}")

            new_ctrls = [
                PatientController(id=c["id"], patient_id=c["patient_id"], physician_id=c["physician_id"], author=c["author"])
                for c in controllers_keep
            ]
            PatientController.objects.bulk_create(new_ctrls, batch_size=500)
            self.stdout.write(f"inserted controllers: {len(new_ctrls)}")

        self.stdout.write(f"smallbrain post-state: teams={PhysicianTeam.objects.count()} controllers={PatientController.objects.count()}")
        self.stdout.write(self.style.SUCCESS("Done."))
