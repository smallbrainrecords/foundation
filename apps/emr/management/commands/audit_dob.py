"""Read-only audit of UserProfile.date_of_birth storage.

Diagnoses the 2019 DateField->DateTimeField regression (migration 0164):
a calendar birth date stored as a midnight timestamp is fragile to any
timezone reinterpretation. This command reports, using RAW SQL (so Django's
USE_TZ conversion does not mask the stored wall-clock value):

  * total rows, null vs non-null DOB
  * distribution of the TIME-of-day component (00:00:00 == clean midnight;
    04:00:00 / 05:00:00 == Detroit UTC offset leaked in on write)
  * a handful of sample raw values
  * birth-year range sanity check

Nothing is written. Safe to run against prod.
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Read-only audit of UserProfile.date_of_birth (no writes)."

    def handle(self, *args, **options):
        with connection.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM emr_userprofile")
            total = cur.fetchone()[0]

            cur.execute(
                "SELECT COUNT(*) FROM emr_userprofile WHERE date_of_birth IS NULL"
            )
            nulls = cur.fetchone()[0]

            non_null = total - nulls
            self.stdout.write("=== DOB audit (raw SQL, bypasses USE_TZ) ===")
            self.stdout.write(f"total profiles      : {total}")
            self.stdout.write(f"date_of_birth NULL  : {nulls}")
            self.stdout.write(f"date_of_birth set   : {non_null}")

            # Time-of-day component distribution.
            self.stdout.write("\n--- TIME(date_of_birth) distribution ---")
            cur.execute(
                "SELECT TIME(date_of_birth) AS t, COUNT(*) AS n "
                "FROM emr_userprofile WHERE date_of_birth IS NOT NULL "
                "GROUP BY t ORDER BY n DESC"
            )
            for t, n in cur.fetchall():
                pct = (n / non_null * 100) if non_null else 0
                self.stdout.write(f"  {str(t):>12}  {n:>6}  ({pct:5.1f}%)")

            # Sample raw values.
            self.stdout.write("\n--- sample raw values (first 15 non-null) ---")
            cur.execute(
                "SELECT user_id, date_of_birth FROM emr_userprofile "
                "WHERE date_of_birth IS NOT NULL ORDER BY user_id LIMIT 15"
            )
            for uid, dob in cur.fetchall():
                self.stdout.write(f"  user_id={uid:>6}  {dob}")

            # Year range sanity.
            self.stdout.write("\n--- birth-year range ---")
            cur.execute(
                "SELECT MIN(YEAR(date_of_birth)), MAX(YEAR(date_of_birth)) "
                "FROM emr_userprofile WHERE date_of_birth IS NOT NULL"
            )
            ymin, ymax = cur.fetchone()
            self.stdout.write(f"  min year: {ymin}   max year: {ymax}")

            # Per-decade tally (data-quality spread).
            self.stdout.write("\n--- per-decade tally ---")
            cur.execute(
                "SELECT (YEAR(date_of_birth) DIV 10) * 10 AS decade, COUNT(*) AS n "
                "FROM emr_userprofile WHERE date_of_birth IS NOT NULL "
                "GROUP BY decade ORDER BY decade"
            )
            for decade, n in cur.fetchall():
                self.stdout.write(f"  {int(decade)}s : {n}")

            # Implausible births: very old (<= 1920) and future / very recent (>= today).
            self.stdout.write("\n--- implausible: birth year <= 1920 ---")
            cur.execute(
                "SELECT user_id, date_of_birth FROM emr_userprofile "
                "WHERE date_of_birth IS NOT NULL AND YEAR(date_of_birth) <= 1920 "
                "ORDER BY date_of_birth LIMIT 50"
            )
            old_rows = cur.fetchall()
            self.stdout.write(f"  count: {len(old_rows)} (showing up to 50)")
            for uid, dob in old_rows:
                self.stdout.write(f"    user_id={uid:>6}  {dob}")

            self.stdout.write("\n--- implausible: DOB in the future ---")
            cur.execute(
                "SELECT user_id, date_of_birth FROM emr_userprofile "
                "WHERE date_of_birth IS NOT NULL AND date_of_birth > NOW() "
                "ORDER BY date_of_birth LIMIT 50"
            )
            future_rows = cur.fetchall()
            self.stdout.write(f"  count: {len(future_rows)}")
            for uid, dob in future_rows:
                self.stdout.write(f"    user_id={uid:>6}  {dob}")

            # Exact 1900-01-01 sentinel check (classic placeholder).
            self.stdout.write("\n--- sentinel: exactly 1900-01-01 ---")
            cur.execute(
                "SELECT COUNT(*) FROM emr_userprofile "
                "WHERE DATE(date_of_birth) = '1900-01-01'"
            )
            self.stdout.write(f"  count: {cur.fetchone()[0]}")

        self.stdout.write(self.style.SUCCESS("\nDONE (read-only, nothing written)."))
