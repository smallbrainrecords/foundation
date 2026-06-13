"""Surgical import of Observation family. Phase 6.
- Wipes SBR1-created Observations + their CASCADE deps (components + values).
- Wipes ALL ObservationPinToProblem (small, replace from legacy).
- Inserts dump's observations, components, values, pins.
- Values created post-cutoff that reference pre-existing components are also inserted.
"""
import json
import os
import tempfile
from datetime import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from emr.models import (
    Observation, ObservationComponent, ObservationValue, ObservationPinToProblem,
    Problem,
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


def _dec(s):
    if s is None or s == "":
        return None
    try:
        return Decimal(s)
    except Exception:
        return None


class Command(BaseCommand):
    help = "Import legacy Observation family. Idempotent."

    def add_arguments(self, parser):
        parser.add_argument("--dump", type=str, required=True)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        dry = options["dry_run"]
        self.stdout.write(f"--- import_obs_family (dry_run={dry}) ---")

        dump = _load_json(options["dump"])
        l_obs = dump["observations"]
        l_comps = dump["components"]
        l_vals = dump["values"]
        l_pins = dump["pins"]
        self.stdout.write(f"dump: obs={len(l_obs)} comps={len(l_comps)} values={len(l_vals)} pins={len(l_pins)}")

        # SBR1 in smallbrain.
        sbr1_obs_ids = set(Observation.objects.filter(created_on__gte=CUTOFF).values_list("id", flat=True))
        sbr1_val_ids = set(ObservationValue.objects.filter(created_on__gte=CUTOFF).values_list("id", flat=True))
        self.stdout.write(f"sbr1_obs_ids={len(sbr1_obs_ids)} sbr1_val_ids={len(sbr1_val_ids)}")

        # FK pre-checks.
        all_user_ids = set(User.objects.values_list("id", flat=True))
        existing_obs_ids = set(Observation.objects.values_list("id", flat=True))
        existing_comp_ids = set(ObservationComponent.objects.values_list("id", flat=True))
        existing_prob_ids = set(Problem.objects.values_list("id", flat=True))

        if dry:
            self.stdout.write(self.style.SUCCESS("DRY RUN done."))
            return

        with transaction.atomic():
            # 1. Wipe SBR1 Observations (CASCADE deletes their components + values).
            del_obs = Observation.objects.filter(id__in=sbr1_obs_ids).delete()
            self.stdout.write(f"wiped SBR1 observations (+ cascade): {del_obs[0]}")

            # 2. Wipe SBR1 values whose obs survived (post-cutoff values attached
            #    to pre-cutoff observations — these are SBR1's standalone value
            #    pushes to existing observations).
            del_vals = ObservationValue.objects.filter(id__in=sbr1_val_ids).delete()
            self.stdout.write(f"wiped SBR1 standalone values: {del_vals[0]}")

            # 3. Wipe ALL ObservationPinToProblem — small table, replace.
            del_pins = ObservationPinToProblem.objects.all().delete()
            self.stdout.write(f"wiped pins: {del_pins[0]}")

            # 4. Also delete legacy-collision-IDs of obs/comp/val that already
            #    exist in smallbrain at the same id (idempotent).
            collide_obs = {o["id"] for o in l_obs} & existing_obs_ids - sbr1_obs_ids
            collide_comp = {c["id"] for c in l_comps} & existing_comp_ids
            collide_val = {v["id"] for v in l_vals} & set(
                ObservationValue.objects.values_list("id", flat=True)
            ) - sbr1_val_ids
            if collide_obs:
                Observation.objects.filter(id__in=collide_obs).delete()
            if collide_comp:
                ObservationComponent.objects.filter(id__in=collide_comp).delete()
            if collide_val:
                ObservationValue.objects.filter(id__in=collide_val).delete()
            self.stdout.write(
                f"wiped collisions: obs={len(collide_obs)} comp={len(collide_comp)} val={len(collide_val)}"
            )

            # 5. Insert Observations. created_on has auto_now_add.
            obs_created = Observation._meta.get_field("created_on")
            obs_created.auto_now_add = False
            try:
                # FK filter on author/subject/performer/encounter (all User FKs, SET_NULL on missing).
                def _u(uid):
                    return uid if uid in all_user_ids else None
                new_obs = [
                    Observation(
                        id=o["id"], name=o["name"], status=o["status"], category=o["category"],
                        code=o["code"],
                        effective_datetime=_parse_dt(o["effective_datetime"]),
                        comments=o["comments"], color=o["color"], graph=o["graph"],
                        subject_id=_u(o["subject_id"]),
                        encounter_id=_u(o["encounter_id"]),
                        performer_id=_u(o["performer_id"]),
                        author_id=_u(o["author_id"]),
                        created_on=_parse_dt(o["created_on"]),
                    )
                    for o in l_obs
                ]
                Observation.objects.bulk_create(new_obs, batch_size=500)
            finally:
                obs_created.auto_now_add = True
            self.stdout.write(f"inserted Observations: {len(new_obs)}")

            # 6. Insert Components. created_on has auto_now_add. FK to observation required.
            now_existing_obs = set(Observation.objects.values_list("id", flat=True))
            comp_created = ObservationComponent._meta.get_field("created_on")
            comp_created.auto_now_add = False
            try:
                new_comps = [
                    ObservationComponent(
                        id=c["id"], name=c["name"], status=c["status"],
                        component_code=c["component_code"],
                        value_quantity=_dec(c["value_quantity"]),
                        value_codeableconcept=c["value_codeableconcept"],
                        value_string=c["value_string"], value_unit=c["value_unit"],
                        comments=c["comments"],
                        effective_datetime=_parse_dt(c["effective_datetime"]),
                        observation_id=c["observation_id"],
                        author_id=_u(c["author_id"]),
                        created_on=_parse_dt(c["created_on"]),
                    )
                    for c in l_comps
                    if c["observation_id"] in now_existing_obs
                ]
                ObservationComponent.objects.bulk_create(new_comps, batch_size=500)
            finally:
                comp_created.auto_now_add = True
            self.stdout.write(f"inserted Components: {len(new_comps)}")

            # 7. Insert Values. created_on has auto_now_add. FK to component required.
            now_existing_comp = set(ObservationComponent.objects.values_list("id", flat=True))
            val_created = ObservationValue._meta.get_field("created_on")
            val_created.auto_now_add = False
            try:
                new_vals = [
                    ObservationValue(
                        id=v["id"], status=v["status"],
                        value_quantity=_dec(v["value_quantity"]),
                        value_codeableconcept=v["value_codeableconcept"],
                        value_string=v["value_string"], value_unit=v["value_unit"],
                        effective_datetime=_parse_dt(v["effective_datetime"]),
                        component_id=v["component_id"],
                        author_id=_u(v["author_id"]),
                        created_on=_parse_dt(v["created_on"]),
                    )
                    for v in l_vals
                    if v["component_id"] in now_existing_comp
                ]
                ObservationValue.objects.bulk_create(new_vals, batch_size=500)
            finally:
                val_created.auto_now_add = True
            val_skip = len(l_vals) - len(new_vals)
            self.stdout.write(f"inserted Values: {len(new_vals)} (skipped {val_skip} FK-orphans)")

            # 8. Insert Pins — FK filter, drop preserved IDs to avoid collisions.
            now_obs = set(Observation.objects.values_list("id", flat=True))
            now_probs = set(Problem.objects.values_list("id", flat=True))
            new_pins = [
                ObservationPinToProblem(
                    author_id=_u(p["author_id"]),
                    observation_id=p["observation_id"] if p["observation_id"] in now_obs else None,
                    problem_id=p["problem_id"] if p["problem_id"] in now_probs else None,
                )
                for p in l_pins
                if p["observation_id"] in now_obs and p["problem_id"] in now_probs
            ]
            ObservationPinToProblem.objects.bulk_create(new_pins, batch_size=500)
            pin_skip = len(l_pins) - len(new_pins)
            self.stdout.write(f"inserted Pins: {len(new_pins)} (skipped {pin_skip} FK-orphans)")

        self.stdout.write(
            f"post-state: obs={Observation.objects.count()} comps={ObservationComponent.objects.count()} "
            f"vals={ObservationValue.objects.count()} pins={ObservationPinToProblem.objects.count()}"
        )
        self.stdout.write(self.style.SUCCESS("Done."))
