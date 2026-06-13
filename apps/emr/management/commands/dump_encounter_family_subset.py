"""Dump the encounter family (Encounter + EncounterEvent + EncounterProblemRecord
+ EncounterTodoRecord + EncounterObservationValue) for a specified list of
encounter IDs to a single JSON file. Used for the 2026-06 surgical migration.

Usage:
    python manage.py dump_encounter_family_subset --ids /tmp/target_ids.json --output /tmp/dump.json
"""
import json

from django.core.management.base import BaseCommand

from emr.models import (
    Encounter,
    EncounterEvent,
    EncounterProblemRecord,
    EncounterTodoRecord,
    EncounterObservationValue,
)


def _enc_to_dict(e):
    return {
        "id": e.id,
        "physician_id": e.physician_id,
        "patient_id": e.patient_id,
        "starttime": e.starttime.isoformat() if e.starttime else None,
        "stoptime": e.stoptime.isoformat() if e.stoptime else None,
        "audio": str(e.audio) if e.audio else "",
        "audio_played_count": e.audio_played_count,
        "recorder_status": e.recorder_status,
        "video": str(e.video) if e.video else "",
        "note": e.note or "",
        "transcript": e.transcript or "",
        "client_uuid": str(e.client_uuid) if e.client_uuid else None,
    }


def _model_to_dict(obj):
    """Generic Django model -> dict; iso-format datetimes; skip private attrs."""
    out = {}
    for f in obj._meta.fields:
        v = getattr(obj, f.attname)
        if hasattr(v, "isoformat"):
            v = v.isoformat()
        elif hasattr(v, "__str__") and f.get_internal_type() == "UUIDField" and v is not None:
            v = str(v)
        out[f.attname] = v
    return out


class Command(BaseCommand):
    help = "Dump encounter family rows for a specified ID list to JSON."

    def add_arguments(self, parser):
        parser.add_argument("--ids", type=str, required=True,
                            help="Path to a JSON file containing a list of encounter IDs.")
        parser.add_argument("--output", type=str, required=True,
                            help="Output JSON path.")

    def handle(self, *args, **options):
        with open(options["ids"]) as f:
            target_ids = json.load(f)
        target_ids = set(int(i) for i in target_ids)

        encs = list(Encounter.objects.filter(id__in=target_ids))
        events = list(EncounterEvent.objects.filter(encounter_id__in=target_ids))
        epr = list(EncounterProblemRecord.objects.filter(encounter_id__in=target_ids))
        etr = list(EncounterTodoRecord.objects.filter(encounter_id__in=target_ids))
        eov = list(EncounterObservationValue.objects.filter(encounter_id__in=target_ids))

        payload = {
            "schema_version": 1,
            "target_ids_count": len(target_ids),
            "encounters": [_enc_to_dict(e) for e in encs],
            "events": [_model_to_dict(e) for e in events],
            "encounter_problem_records": [_model_to_dict(r) for r in epr],
            "encounter_todo_records": [_model_to_dict(r) for r in etr],
            "encounter_observation_values": [_model_to_dict(r) for r in eov],
        }

        with open(options["output"], "w") as f:
            json.dump(payload, f, default=str)

        self.stdout.write(
            f"Dumped: encounters={len(encs)} events={len(events)} "
            f"epr={len(epr)} etr={len(etr)} eov={len(eov)} -> {options['output']}"
        )
