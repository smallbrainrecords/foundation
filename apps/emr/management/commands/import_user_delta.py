"""Surgical import of legacy User + UserProfile delta into smallbrain-db.

For the 2026-06-10 migration phase 2: inserts the 3 users that exist on
legacy but not in smallbrain (user IDs > smallbrain's current max). Idempotent.
"""
import json
import os
import tempfile
from datetime import datetime

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from emr.models import UserProfile


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
    help = "Import legacy User + UserProfile delta. Idempotent."

    def add_arguments(self, parser):
        parser.add_argument("--dump", type=str, required=True)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        dry = options["dry_run"]
        self.stdout.write(f"--- import_user_delta (dry_run={dry}) ---")

        dump = _load_json(options["dump"])
        users = dump["users"]
        profiles = dump["userprofiles"]
        self.stdout.write(f"dump: users={len(users)} profiles={len(profiles)}")

        if not users:
            self.stdout.write(self.style.WARNING("dump has no users; nothing to do"))
            return

        target_ids = {u["id"] for u in users}
        existing = set(User.objects.filter(id__in=target_ids).values_list("id", flat=True))
        self.stdout.write(f"smallbrain pre-state: target_ids_already_present={len(existing)}/{len(target_ids)}")

        if dry:
            self.stdout.write(self.style.SUCCESS("DRY RUN done."))
            return

        with transaction.atomic():
            # Idempotent: delete any already-present rows so re-runs work.
            if existing:
                UserProfile.objects.filter(user_id__in=existing).delete()
                User.objects.filter(id__in=existing).delete()
                self.stdout.write(f"cleaned up {len(existing)} pre-existing rows for idempotent re-run")

            # Insert users. date_joined has auto_now_add — disable temporarily.
            date_joined_field = User._meta.get_field("date_joined")
            date_joined_field.auto_now_add = False
            try:
                new_users = [
                    User(
                        id=u["id"],
                        username=u["username"],
                        password=u["password"],
                        email=u["email"],
                        first_name=u["first_name"],
                        last_name=u["last_name"],
                        is_active=u["is_active"],
                        is_staff=u["is_staff"],
                        is_superuser=u["is_superuser"],
                        date_joined=_parse_dt(u["date_joined"]),
                        last_login=_parse_dt(u["last_login"]),
                    )
                    for u in users
                ]
                User.objects.bulk_create(new_users)
            finally:
                date_joined_field.auto_now_add = True
            self.stdout.write(f"inserted users: {len(new_users)}")

            # Insert profiles.
            new_profiles = [
                UserProfile(
                    id=p["id"],
                    user_id=p["user_id"],
                    role=p["role"],
                    data=p.get("data", ""),
                    cover_image=p.get("cover_image", ""),
                    portrait_image=p.get("portrait_image", ""),
                    summary=p.get("summary", ""),
                    sex=p.get("sex", ""),
                    date_of_birth=_parse_dt(p.get("date_of_birth")),
                    deceased_date=_parse_dt(p.get("deceased_date")),
                    marital_status_id=p.get("marital_status_id"),
                    phone_number=p.get("phone_number", ""),
                    note=p.get("note", ""),
                    active_reason=p.get("active_reason", ""),
                    inr_target=p.get("inr_target", 1),
                    last_access_tagged_todo=_parse_dt(p.get("last_access_tagged_todo")),
                    insurance_medicare=p.get("insurance_medicare", False),
                    insurance_note=p.get("insurance_note", ""),
                )
                for p in profiles
            ]
            UserProfile.objects.bulk_create(new_profiles)
            self.stdout.write(f"inserted profiles: {len(new_profiles)}")
            self.stdout.write(self.style.SUCCESS("Transaction will commit on handler exit."))

        new_total = User.objects.count()
        new_profile_total = UserProfile.objects.count()
        self.stdout.write(f"smallbrain post-state: user_total={new_total} profile_total={new_profile_total}")
        self.stdout.write(self.style.SUCCESS("Done."))
