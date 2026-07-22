from django.db import migrations


# Cluster B1 backfill (PLAN_PATIENT_ACCESS_AND_DECODE_2026-07): the mobile
# register endpoint historically created User + UserProfile but never the
# PatientController row — the row that puts a patient on /api/patients/ and
# that _assert_patient_access requires. Sized against the 2026-07-22 prod
# clone: exactly 16 role='patient' users had no controller row (the two Abby
# Butler accounts 3772/3773, 12 legacy-era patients from 2014-2022, and 2
# test accounts). This links them all to the practice physician so every
# server patient is reachable; mobile_register now creates the row at
# creation time, so the population cannot regrow.
BACKFILL_PHYSICIAN_USERNAME = 'ryanjam4@msu.edu'

# Owner decision 2026-07-22: 3772 (abbutler) is the canonical Abby Butler —
# it carries her real charting. 3773 (AbbyButler) is the empty accidental
# duplicate from a re-add under a respelled username; it is excluded from
# the backfill AND deactivated below so exactly one Abby exists everywhere.
EXCLUDE_USER_IDS = [3773]

# (user_id, exact username) pairs to deactivate — both must match, so this
# can only ever touch the intended prod row and no-ops everywhere else.
RETIRE_ACCOUNTS = [(3773, 'AbbyButler')]


def backfill_controllers(apps, schema_editor):
    """Idempotent: only touches patients with zero controller rows. No-ops
    entirely when the practice physician doesn't exist (fresh schemas, test
    databases) — those environments have no unlinked legacy patients to
    repair, and creating rows against a hardcoded username there would be
    meaningless. Safe under the boot-time auto-migrate deploy."""
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('emr', 'UserProfile')
    PatientController = apps.get_model('emr', 'PatientController')

    physician = User.objects.filter(
        username=BACKFILL_PHYSICIAN_USERNAME,
        profile__role='physician',
    ).first()
    if physician is None:
        return

    linked_ids = set(
        PatientController.objects.values_list('patient_id', flat=True))
    unlinked = (
        UserProfile.objects.filter(role='patient')
        .exclude(user_id__in=linked_ids)
        .exclude(user_id__in=EXCLUDE_USER_IDS)
        .values_list('user_id', flat=True)
    )
    PatientController.objects.bulk_create([
        PatientController(patient_id=uid, physician_id=physician.id)
        for uid in unlinked
    ])

    for uid, uname in RETIRE_ACCOUNTS:
        User.objects.filter(
            id=uid, username=uname, is_active=True,
        ).update(is_active=False)


class Migration(migrations.Migration):
    """Data-only. Reverse is a deliberate no-op: unlinking patients from the
    roster is exactly the failure mode this repairs, so an automated reverse
    would be a clinical-safety hazard."""

    dependencies = [
        ('emr', '0184_userprofile_client_uuid'),
    ]

    operations = [
        migrations.RunPython(
            backfill_controllers, migrations.RunPython.noop),
    ]
