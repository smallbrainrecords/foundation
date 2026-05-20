"""
Copy PhysicianTeam (and optionally PatientController) records from an old
database to the current Django default database, matching users by username.

Usage (local old DB → local current DB):
    python manage.py sync_team --old-db andromeda_redacted

Usage (local old DB → GCP prod, via Cloud SQL proxy):
    DJANGO_SETTINGS_MODULE=project.settings_prod \
    python manage.py sync_team --old-db andromeda_redacted --old-host 127.0.0.1
"""
import MySQLdb
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from emr.models import PhysicianTeam, PatientController


class Command(BaseCommand):
    help = "Copy PhysicianTeam and PatientController records from an old database"

    def add_arguments(self, parser):
        parser.add_argument("--old-db", required=True, help="Old database name")
        parser.add_argument("--old-host", default="127.0.0.1")
        parser.add_argument("--old-port", type=int, default=3306)
        parser.add_argument("--old-user", default="root")
        parser.add_argument("--old-password", default="")
        parser.add_argument("--dry-run", action="store_true", help="Show what would be copied without writing")
        parser.add_argument("--skip-patient-controller", action="store_true", help="Skip PatientController sync")

    def handle(self, *args, **options):
        conn_kwargs = dict(
            host=options["old_host"],
            port=options["old_port"],
            user=options["old_user"],
            db=options["old_db"],
        )
        if options["old_password"]:
            conn_kwargs["passwd"] = options["old_password"]

        conn = MySQLdb.connect(**conn_kwargs)
        cursor = conn.cursor()

        # Build username lookup for current DB
        current_users = {u.username: u for u in User.objects.filter(is_active=True)}
        self.stdout.write(f"Current DB has {len(current_users)} active users")

        # --- PhysicianTeam ---
        cursor.execute("""
            SELECT
                phys.username AS physician_username,
                mem.username  AS member_username
            FROM emr_physicianteam pt
            JOIN auth_user phys ON phys.id = pt.physician_id
            JOIN auth_user mem  ON mem.id  = pt.member_id
        """)
        team_rows = cursor.fetchall()
        self.stdout.write(f"\nOld DB has {len(team_rows)} PhysicianTeam records")

        created_team = 0
        skipped_team = 0
        missing_users = set()

        for physician_username, member_username in team_rows:
            physician = current_users.get(physician_username)
            member = current_users.get(member_username)

            if not physician:
                missing_users.add(physician_username)
                continue
            if not member:
                missing_users.add(member_username)
                continue

            exists = PhysicianTeam.objects.filter(
                physician=physician, member=member
            ).exists()

            if exists:
                skipped_team += 1
                continue

            if options["dry_run"]:
                self.stdout.write(f"  [DRY RUN] Would create: {physician_username} → {member_username}")
            else:
                PhysicianTeam.objects.create(physician=physician, member=member)
            created_team += 1

        self.stdout.write(f"PhysicianTeam: {created_team} created, {skipped_team} already existed")

        # --- PatientController ---
        if not options["skip_patient_controller"]:
            cursor.execute("""
                SELECT
                    pat.username  AS patient_username,
                    phys.username AS physician_username,
                    pc.author
                FROM emr_patientcontroller pc
                JOIN auth_user pat  ON pat.id  = pc.patient_id
                JOIN auth_user phys ON phys.id = pc.physician_id
            """)
            pc_rows = cursor.fetchall()
            self.stdout.write(f"\nOld DB has {len(pc_rows)} PatientController records")

            created_pc = 0
            skipped_pc = 0

            for patient_username, physician_username, author_flag in pc_rows:
                patient = current_users.get(patient_username)
                physician = current_users.get(physician_username)

                if not patient:
                    missing_users.add(patient_username)
                    continue
                if not physician:
                    missing_users.add(physician_username)
                    continue

                exists = PatientController.objects.filter(
                    patient=patient, physician=physician
                ).exists()

                if exists:
                    skipped_pc += 1
                    continue

                if options["dry_run"]:
                    self.stdout.write(f"  [DRY RUN] Would create: patient={patient_username} physician={physician_username}")
                else:
                    PatientController.objects.create(
                        patient=patient, physician=physician, author=author_flag
                    )
                created_pc += 1

            self.stdout.write(f"PatientController: {created_pc} created, {skipped_pc} already existed")

        if missing_users:
            self.stdout.write(self.style.WARNING(
                f"\nUsers in old DB but not in current DB: {sorted(missing_users)}"
            ))
            self.stdout.write("You may need to create these users first (via AddUserView or manage.py).")

        cursor.close()
        conn.close()

        if options["dry_run"]:
            self.stdout.write(self.style.NOTICE("\nDry run complete — no changes written."))
        else:
            self.stdout.write(self.style.SUCCESS("\nSync complete."))
