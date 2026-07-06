"""Per-patient mutation stamp — the change signal behind the mobile
check-mode poll (`GET /api/patient/<pid>/changed`).

Lives in its own module (not problems_app/todo_app operations) so it can be
imported by mobile_api views AND both operations modules without cycles.
"""
import logging

from django.db import IntegrityError, transaction
from django.utils import timezone

from emr.models import PatientMutationStamp

logger = logging.getLogger(__name__)


def touch_patient_stamp(patient_or_id):
    """Record "something about this patient's chart changed, now".

    Accepts a User instance, a pk, or None (no-op). Best-effort by contract:
    a stamp failure must never fail the clinical write that triggered it, so
    errors are logged and swallowed. The UPDATE-first shape means the steady
    state is one indexed UPDATE; the create path only runs once per patient
    ever, with a savepoint so a concurrent-first-write IntegrityError can't
    poison the caller's transaction.
    """
    if not patient_or_id:
        return
    pid = getattr(patient_or_id, 'pk', patient_or_id)
    now = timezone.now()
    try:
        # The whole body runs inside its own atomic block (a savepoint when
        # the caller is already in @transaction.atomic), so ANY DB error here
        # rolls back only the stamp attempt and can't poison the caller's
        # transaction — the swallow below is then actually safe.
        with transaction.atomic():
            if PatientMutationStamp.objects.filter(patient_id=pid).update(last_mutation_at=now):
                return
            try:
                with transaction.atomic():
                    PatientMutationStamp.objects.create(patient_id=pid, last_mutation_at=now)
            except IntegrityError:
                # Lost the concurrent-first-write race (or bogus patient id —
                # then this update is a harmless no-op).
                PatientMutationStamp.objects.filter(patient_id=pid).update(last_mutation_at=now)
    except Exception:
        logger.exception('touch_patient_stamp failed for patient %s (non-fatal)', pid)
