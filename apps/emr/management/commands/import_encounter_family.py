"""Surgical import of legacy encounter family rows into smallbrain-db.

For the 2026-06-10 migration:
  - Deletes the 22 SBR1-iOS-created encounters in smallbrain-db (and their
    dependent EncounterEvent rows; CASCADE handles the join tables).
  - Inserts 250 legacy encounters (22 collision IDs + 228 legacy-only IDs),
    preserving the legacy primary keys.
  - Inserts their EncounterEvent rows, preserving IDs.
  - Inserts join-table rows (EncounterProblemRecord, EncounterTodoRecord,
    EncounterObservationValue) — but only where the OTHER FK target (Problem,
    Todo, ObservationValue) already exists in smallbrain-db. Unresolvable join
    rows are reported in stdout and skipped.

All operations are wrapped in a single MySQL transaction. Failure rolls back
cleanly. A read-only --dry-run mode reports what WOULD happen without writing.

Usage:
    python manage.py import_encounter_family --dump gs://.../dump.json \\
        --sbr1-ids gs://.../sbr1_ids.json --dry-run
    python manage.py import_encounter_family --dump gs://.../dump.json \\
        --sbr1-ids gs://.../sbr1_ids.json
"""
import json
import os
import tempfile
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import transaction

from django.contrib.auth.models import User

from emr.models import (
    Encounter,
    EncounterEvent,
    EncounterProblemRecord,
    EncounterTodoRecord,
    EncounterObservationValue,
    Problem,
    ToDo,
    ObservationValue,
)


def _load_json(path):
    """Load a local JSON file or gs:// URI."""
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
    help = "Surgically import legacy encounters into smallbrain-db, replacing SBR1-created rows."

    def add_arguments(self, parser):
        parser.add_argument("--dump", type=str, required=True,
                            help="Path or gs:// URI to legacy dump JSON.")
        parser.add_argument("--sbr1-ids", type=str, required=True,
                            help="Path or gs:// URI to JSON list of smallbrain SBR1 encounter IDs to delete.")
        parser.add_argument("--dry-run", action="store_true",
                            help="Report what would be done without writing to the DB.")

    def handle(self, *args, **options):
        dry = options["dry_run"]
        self.stdout.write(f"--- import_encounter_family (dry_run={dry}) ---")

        dump = _load_json(options["dump"])
        sbr1_ids = set(int(i) for i in _load_json(options["sbr1_ids"]))

        legacy_encs = dump["encounters"]
        legacy_events = dump["events"]
        legacy_epr = dump["encounter_problem_records"]
        legacy_etr = dump["encounter_todo_records"]
        legacy_eov = dump["encounter_observation_values"]

        dump_enc_ids = set(e["id"] for e in legacy_encs)

        self.stdout.write(
            f"dump: encs={len(legacy_encs)} events={len(legacy_events)} "
            f"epr={len(legacy_epr)} etr={len(legacy_etr)} eov={len(legacy_eov)}"
        )
        self.stdout.write(f"sbr1_ids to delete from smallbrain: {len(sbr1_ids)}")

        # Sanity checks before doing anything destructive.
        if not sbr1_ids:
            raise SystemExit("ERROR: sbr1-ids list is empty. Refusing to proceed.")
        if not legacy_encs:
            raise SystemExit("ERROR: dump has no encounters. Refusing to proceed.")
        if not (sbr1_ids <= dump_enc_ids):
            missing = sbr1_ids - dump_enc_ids
            raise SystemExit(
                f"ERROR: sbr1_ids contains {len(missing)} IDs not in the legacy dump "
                f"(would lose replacement rows). Sample: {sorted(missing)[:10]}"
            )

        # Pre-flight smallbrain-db state.
        sbr1_in_db = Encounter.objects.filter(id__in=sbr1_ids).count()
        events_to_delete = EncounterEvent.objects.filter(encounter_id__in=sbr1_ids).count()
        self.stdout.write(
            f"smallbrain pre-state: sbr1_encounters_found={sbr1_in_db}/{len(sbr1_ids)} "
            f"dependent_events={events_to_delete}"
        )
        if sbr1_in_db != len(sbr1_ids):
            self.stdout.write(self.style.WARNING(
                f"  ({len(sbr1_ids) - sbr1_in_db} SBR1 ids in input not found in DB — "
                f"continuing; missing rows are no-op deletes)"
            ))

        # Filter encounters whose patient_id or physician_id doesn't exist in
        # smallbrain's auth_user (legacy added users post-dump that aren't
        # migrated yet). Skipped encounters + their dependents will be
        # backfilled in a future migration round.
        all_user_ids = {e["patient_id"] for e in legacy_encs} | {e["physician_id"] for e in legacy_encs}
        existing_user_ids = set(User.objects.filter(id__in=all_user_ids).values_list("id", flat=True))
        keepable_enc_ids = {
            e["id"] for e in legacy_encs
            if e["patient_id"] in existing_user_ids and e["physician_id"] in existing_user_ids
        }
        legacy_encs_keep = [e for e in legacy_encs if e["id"] in keepable_enc_ids]
        enc_skip = len(legacy_encs) - len(legacy_encs_keep)
        self.stdout.write(
            f"FK filter: keepable_encounters={len(legacy_encs_keep)} (skip {enc_skip} "
            f"with missing patient/physician)"
        )

        # Cascade-filter dependents to only those whose encounter survives.
        legacy_events = [ev for ev in legacy_events if ev["encounter_id"] in keepable_enc_ids]
        legacy_epr = [r for r in legacy_epr if r["encounter_id"] in keepable_enc_ids]
        legacy_etr = [r for r in legacy_etr if r["encounter_id"] in keepable_enc_ids]
        legacy_eov = [r for r in legacy_eov if r["encounter_id"] in keepable_enc_ids]

        # Filter join rows to those whose OTHER FK target exists in smallbrain.
        existing_problem_ids = set(Problem.objects.filter(
            id__in={r["problem_id"] for r in legacy_epr}
        ).values_list("id", flat=True))
        epr_keep = [r for r in legacy_epr if r["problem_id"] in existing_problem_ids]
        epr_skip = len(legacy_epr) - len(epr_keep)

        existing_todo_ids = set(ToDo.objects.filter(
            id__in={r["todo_id"] for r in legacy_etr}
        ).values_list("id", flat=True))
        etr_keep = [r for r in legacy_etr if r["todo_id"] in existing_todo_ids]
        etr_skip = len(legacy_etr) - len(etr_keep)

        existing_obs_ids = set(ObservationValue.objects.filter(
            id__in={r["observation_value_id"] for r in legacy_eov}
        ).values_list("id", flat=True))
        eov_keep = [r for r in legacy_eov if r["observation_value_id"] in existing_obs_ids]
        eov_skip = len(legacy_eov) - len(eov_keep)

        self.stdout.write(
            f"join filter: epr_keep={len(epr_keep)} (skip {epr_skip}) "
            f"etr_keep={len(etr_keep)} (skip {etr_skip}) "
            f"eov_keep={len(eov_keep)} (skip {eov_skip})"
        )

        if dry:
            self.stdout.write(self.style.SUCCESS("DRY RUN complete. Nothing written."))
            return

        # Execute under a single transaction.
        with transaction.atomic():
            # 1. Delete EncounterEvent rows for SBR1 encounters AND for any
            #    existing rows at our target IDs (idempotent re-runs). The FK
            #    is SET_NULL — explicit delete avoids orphans.
            cleanup_ids = sbr1_ids | keepable_enc_ids
            del_events, _ = EncounterEvent.objects.filter(encounter_id__in=cleanup_ids).delete()
            # 2. Delete Encounter rows at SBR1 IDs AND at any target IDs that
            #    already exist (idempotency). CASCADE cleans the join tables.
            del_encs, _ = Encounter.objects.filter(id__in=cleanup_ids).delete()
            self.stdout.write(f"deleted: events={del_events} encounters={del_encs}")

            # 3. Insert Encounter rows. starttime has auto_now_add=True which
            #    overrides explicit values even under bulk_create. Temporarily
            #    flip auto_now_add off so the legacy starttimes are preserved.
            enc_starttime_field = Encounter._meta.get_field("starttime")
            enc_starttime_field.auto_now_add = False
            try:
                new_encs = [
                    Encounter(
                        id=e["id"],
                        physician_id=e["physician_id"],
                        patient_id=e["patient_id"],
                        starttime=_parse_dt(e["starttime"]),
                        stoptime=_parse_dt(e["stoptime"]),
                        audio=e["audio"],
                        audio_played_count=e["audio_played_count"],
                        recorder_status=e["recorder_status"],
                        video=e["video"],
                        note=e["note"],
                        transcript=e["transcript"],
                        client_uuid=e["client_uuid"],
                    )
                    for e in legacy_encs_keep
                ]
                Encounter.objects.bulk_create(new_encs, batch_size=500)
            finally:
                enc_starttime_field.auto_now_add = True
            self.stdout.write(f"inserted encounters: {len(new_encs)}")

            # 4. EncounterEvents — `datetime` also has auto_now_add. Same fix.
            event_datetime_field = EncounterEvent._meta.get_field("datetime")
            event_datetime_field.auto_now_add = False
            try:
                new_events = [
                    EncounterEvent(
                        id=ev["id"],
                        encounter_id=ev["encounter_id"],
                        datetime=_parse_dt(ev.get("datetime")),
                        summary=ev.get("summary", ""),
                        is_favorite=ev.get("is_favorite", False),
                        name_favorite=ev.get("name_favorite"),
                        timestamp=_parse_dt(ev.get("timestamp")),
                        client_uuid=ev.get("client_uuid"),
                    )
                    for ev in legacy_events
                ]
                EncounterEvent.objects.bulk_create(new_events, batch_size=1000)
            finally:
                event_datetime_field.auto_now_add = True
            self.stdout.write(f"inserted events: {len(new_events)}")

            # 5. Join tables — DO NOT preserve IDs. Legacy + smallbrain both
            #    advanced auto-increment past the dump, so dump IDs can collide
            #    with rows for non-target encounters. Auto-assign IDs; the
            #    semantic link (encounter_id + problem/todo_id) is preserved.
            new_epr = [
                EncounterProblemRecord(
                    encounter_id=r["encounter_id"],
                    problem_id=r["problem_id"],
                )
                for r in epr_keep
            ]
            EncounterProblemRecord.objects.bulk_create(new_epr, batch_size=500)
            self.stdout.write(f"inserted EncounterProblemRecord: {len(new_epr)} (skipped {epr_skip})")

            new_etr = [
                EncounterTodoRecord(
                    encounter_id=r["encounter_id"],
                    todo_id=r["todo_id"],
                )
                for r in etr_keep
            ]
            EncounterTodoRecord.objects.bulk_create(new_etr, batch_size=500)
            self.stdout.write(f"inserted EncounterTodoRecord: {len(new_etr)} (skipped {etr_skip})")

            # EOV also has auto_now_add on `created_on`.
            eov_created_field = EncounterObservationValue._meta.get_field("created_on")
            eov_created_field.auto_now_add = False
            try:
                new_eov = [
                    EncounterObservationValue(
                        encounter_id=r["encounter_id"],
                        observation_value_id=r["observation_value_id"],
                        created_on=_parse_dt(r.get("created_on")),
                    )
                    for r in eov_keep
                ]
                EncounterObservationValue.objects.bulk_create(new_eov, batch_size=500)
            finally:
                eov_created_field.auto_now_add = True
            self.stdout.write(f"inserted EncounterObservationValue: {len(new_eov)} (skipped {eov_skip})")

            self.stdout.write(self.style.SUCCESS(
                "All bulk_creates committed. Transaction will commit on handler exit."
            ))

        # Post-state.
        new_total = Encounter.objects.count()
        new_max = Encounter.objects.order_by("-id").first().id
        new_events_total = EncounterEvent.objects.count()
        self.stdout.write(
            f"smallbrain post-state: encounter_total={new_total} max_id={new_max} "
            f"event_total={new_events_total}"
        )
        self.stdout.write(self.style.SUCCESS("Done."))
