#!/usr/bin/env bash
# refresh_testdb.sh — re-clone the prod Cloud SQL database into the local
# Homebrew MySQL test bed (`smallbrain2` on :3306, root / no password).
#
# What it does:
#   1. Exports the prod DB via `gcloud sql export sql --offload` (serverless
#      export: zero read load on the prod instance). Media/audio are NOT
#      copied — files live in GCS and the dump only carries their paths.
#   2. Downloads the dump, then immediately deletes it from the bucket
#      (the dump is PHI; it should exist in GCS for minutes, not days).
#   3. Drops + recreates the local DB and imports, stripping DEFINER/GTID
#      statements that break a prod-8.x -> local-9.x import.
#   4. Truncates django_session and analytics_app_userevent (bulk, irrelevant
#      to app testing).
#   5. Deletes the local dump and prints a freshness summary + next steps.
#
# Prereqs:
#   - `gcloud auth login` run recently in an INTERACTIVE terminal (tokens
#     expire and cannot re-prompt from a script).
#   - Homebrew MySQL running on 3306 (`brew services start mysql`).
#
# Env overrides: PROJECT, INSTANCE, PROD_DB, LOCAL_DB, BUCKET
set -euo pipefail

GCLOUD=/opt/homebrew/bin/gcloud
MYSQL=/opt/homebrew/bin/mysql
PROJECT="${PROJECT:-smallbrain-prod}"
INSTANCE="${INSTANCE:-smallbrain-db}"
LOCAL_DB="${LOCAL_DB:-smallbrain2}"
BUCKET="${BUCKET:-gs://smallbrain-prod-db-exports}"

# --- Preflight -------------------------------------------------------------
if ! "$GCLOUD" auth print-access-token >/dev/null 2>&1; then
    echo "ERROR: gcloud auth is stale. Run 'gcloud auth login' in an interactive terminal, then re-run." >&2
    exit 1
fi
if ! "$MYSQL" -u root -e "SELECT 1" >/dev/null 2>&1; then
    echo "ERROR: local MySQL on 3306 not reachable. Try: brew services start mysql" >&2
    exit 1
fi

# The instance also hosts `snomedct` (static reference data, already imported
# locally) — only the app DB needs refreshing.
PROD_DB="${PROD_DB:-smallbrain2}"
echo "Prod database: $PROD_DB  ->  local: $LOCAL_DB"

# --- Ensure export bucket exists and the instance SA can write to it -------
if ! "$GCLOUD" storage buckets describe "$BUCKET" --project="$PROJECT" >/dev/null 2>&1; then
    echo "Creating export bucket $BUCKET ..."
    "$GCLOUD" storage buckets create "$BUCKET" --project="$PROJECT" \
        --location=us-east5 --uniform-bucket-level-access
fi
SA=$("$GCLOUD" sql instances describe "$INSTANCE" --project="$PROJECT" \
    --format='value(serviceAccountEmailAddress)')
"$GCLOUD" storage buckets add-iam-policy-binding "$BUCKET" \
    --member="serviceAccount:$SA" --role=roles/storage.objectAdmin >/dev/null

# --- Export + download + delete from bucket --------------------------------
STAMP=$(date +%Y%m%d-%H%M%S)
OBJ="$BUCKET/testdb/${PROD_DB}-${STAMP}.sql.gz"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

echo "Exporting (serverless offload; takes a few minutes) ..."
"$GCLOUD" sql export sql "$INSTANCE" "$OBJ" --database="$PROD_DB" --offload --project="$PROJECT"

echo "Downloading dump ..."
"$GCLOUD" storage cp "$OBJ" "$TMP/dump.sql.gz"
echo "Deleting dump from bucket (PHI hygiene) ..."
"$GCLOUD" storage rm "$OBJ"

# --- Recreate local DB and import -------------------------------------------
echo "Recreating local database $LOCAL_DB ..."
"$MYSQL" -u root -e "DROP DATABASE IF EXISTS \`$LOCAL_DB\`; CREATE DATABASE \`$LOCAL_DB\` CHARACTER SET utf8mb4;"

# Strip statements that break cross-version import:
#   - GTID_PURGED / SQL_LOG_BIN session bits (local server has GTID off)
#   - DEFINER clauses (prod user doesn't exist locally)
#   - CREATE DATABASE / USE (we import into $LOCAL_DB explicitly, whatever
#     the prod name is)
# LC_ALL=C so BSD sed tolerates non-UTF8 bytes inside data rows.
echo "Importing ..."
gunzip -c "$TMP/dump.sql.gz" \
    | LC_ALL=C sed -E \
        -e '/@@GLOBAL\.GTID_PURGED/d' \
        -e '/@@SESSION\.SQL_LOG_BIN/d' \
        -e '/^CREATE DATABASE /d' \
        -e '/^USE /d' \
        -e 's/DEFINER=`[^`]+`@`[^`]+`//g' \
    | "$MYSQL" -u root --max-allowed-packet=512M "$LOCAL_DB"

echo "Scrubbing bulk/irrelevant tables ..."
for t in django_session analytics_app_userevent; do
    "$MYSQL" -u root -e "TRUNCATE TABLE \`$t\`;" "$LOCAL_DB" 2>/dev/null \
        || echo "  (skip: $t not present)"
done

# --- Summary ----------------------------------------------------------------
echo
echo "Done. Freshness check:"
"$MYSQL" -u root -t -e "
    SELECT
        (SELECT COUNT(*) FROM auth_user)                       AS users,
        (SELECT COUNT(*) FROM emr_problem)                     AS problems,
        (SELECT MAX(created_on) FROM emr_problemactivity)      AS newest_activity;
" "$LOCAL_DB"

cat <<'EOF'

Next steps:
  Rehearse migrations : .venv312/bin/python manage.py migrate --settings=project._testbed_settings
  Run the server      : scripts/run_testbed.sh              (binds 127.0.0.1:8000)
  Point the app at it : set the Server URL on the login screen to http://127.0.0.1:8000
EOF
