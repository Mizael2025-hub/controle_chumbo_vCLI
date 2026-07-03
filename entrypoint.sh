#!/bin/sh
set -e

echo "==> Waiting for database..."
python manage.py wait_for_db --timeout 90

echo "==> Migrate (pg_try_advisory_lock)..."
python - <<'PY'
import os, sys, time
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django
django.setup()
from django.db import connection
with connection.cursor() as cur:
    for i in range(120):
        cur.execute("SELECT pg_try_advisory_lock(1)")
        if cur.fetchone()[0]:
            print("Advisory lock acquired.")
            break
        time.sleep(1)
    else:
        print("Could not acquire advisory lock after 120s.")
        sys.exit(1)
try:
    from django.core.management import call_command
    call_command("migrate", interactive=False, verbosity=1)
finally:
    with connection.cursor() as cur:
        cur.execute("SELECT pg_advisory_unlock(1)")
    print("Advisory lock released.")
PY

echo "==> Collectstatic..."
python manage.py collectstatic --noinput --clear

echo "==> Start: $@"
exec "$@"
