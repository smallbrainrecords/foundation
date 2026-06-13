"""Import MyStory family. Phase 7."""
import json
import os
import tempfile
from datetime import datetime

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from emr.models import MyStoryTab, MyStoryTextComponent, MyStoryTextComponentEntry

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
        self.stdout.write(f"--- import_mystory_family (dry_run={dry}) ---")

        dump = _load_json(options["dump"])
        tabs = dump["tabs"]
        comps = dump["components"]
        entries = dump["entries"]
        self.stdout.write(f"dump: tabs={len(tabs)} comps={len(comps)} entries={len(entries)}")

        all_user_ids = set(User.objects.values_list("id", flat=True))
        sbr1_entry_ids = set(
            MyStoryTextComponentEntry.objects.filter(datetime__gte=CUTOFF).values_list("id", flat=True)
        )
        self.stdout.write(f"sbr1 entries to wipe: {len(sbr1_entry_ids)}")

        if dry:
            self.stdout.write(self.style.SUCCESS("DRY RUN done."))
            return

        with transaction.atomic():
            # 1. Wipe SBR1-created entries.
            del_e = MyStoryTextComponentEntry.objects.filter(id__in=sbr1_entry_ids).delete()
            self.stdout.write(f"wiped SBR1 entries: {del_e[0]}")

            # 2. Insert missing Tabs.
            existing_tab_ids = set(MyStoryTab.objects.values_list("id", flat=True))
            tab_dt_field = MyStoryTab._meta.get_field("datetime")
            tab_dt_field.auto_now_add = False
            try:
                new_tabs = [
                    MyStoryTab(
                        id=t["id"], name=t["name"], private=t["private"], is_all=t["is_all"],
                        patient_id=t["patient_id"] if t["patient_id"] in all_user_ids else None,
                        author_id=t["author_id"] if t["author_id"] in all_user_ids else None,
                        datetime=_parse_dt(t["datetime"]),
                    )
                    for t in tabs
                    if t["id"] not in existing_tab_ids
                    and t["patient_id"] in all_user_ids
                ]
                MyStoryTab.objects.bulk_create(new_tabs)
            finally:
                tab_dt_field.auto_now_add = True
            self.stdout.write(f"inserted Tabs: {len(new_tabs)}")

            # 3. Insert missing Components.
            now_tab_ids = set(MyStoryTab.objects.values_list("id", flat=True))
            existing_comp_ids = set(MyStoryTextComponent.objects.values_list("id", flat=True))
            comp_dt_field = MyStoryTextComponent._meta.get_field("datetime")
            comp_dt_field.auto_now_add = False
            try:
                new_comps = [
                    MyStoryTextComponent(
                        id=c["id"], name=c["name"], concept_id=c["concept_id"],
                        private=c["private"], is_all=c["is_all"],
                        tab_id=c["tab_id"] if c["tab_id"] in now_tab_ids else None,
                        patient_id=c["patient_id"] if c["patient_id"] in all_user_ids else None,
                        author_id=c["author_id"] if c["author_id"] in all_user_ids else None,
                        datetime=_parse_dt(c["datetime"]),
                    )
                    for c in comps
                    if c["id"] not in existing_comp_ids
                    and c["patient_id"] in all_user_ids
                ]
                MyStoryTextComponent.objects.bulk_create(new_comps)
            finally:
                comp_dt_field.auto_now_add = True
            self.stdout.write(f"inserted Components: {len(new_comps)}")

            # 4. Insert Entries.
            now_comp_ids = set(MyStoryTextComponent.objects.values_list("id", flat=True))
            entry_dt_field = MyStoryTextComponentEntry._meta.get_field("datetime")
            entry_dt_field.auto_now_add = False
            try:
                existing_entry_ids = set(
                    MyStoryTextComponentEntry.objects.filter(
                        id__in={e["id"] for e in entries}
                    ).values_list("id", flat=True)
                )
                new_entries = [
                    MyStoryTextComponentEntry(
                        id=e["id"], text=e["text"],
                        component_id=e["component_id"] if e["component_id"] in now_comp_ids else None,
                        patient_id=e["patient_id"] if e["patient_id"] in all_user_ids else None,
                        author_id=e["author_id"] if e["author_id"] in all_user_ids else None,
                        datetime=_parse_dt(e["datetime"]),
                    )
                    for e in entries
                    if e["id"] not in existing_entry_ids
                ]
                MyStoryTextComponentEntry.objects.bulk_create(new_entries, batch_size=500)
            finally:
                entry_dt_field.auto_now_add = True
            self.stdout.write(f"inserted Entries: {len(new_entries)}")

        self.stdout.write(
            f"post-state: tabs={MyStoryTab.objects.count()} "
            f"comps={MyStoryTextComponent.objects.count()} "
            f"entries={MyStoryTextComponentEntry.objects.count()}"
        )
        self.stdout.write(self.style.SUCCESS("Done."))
