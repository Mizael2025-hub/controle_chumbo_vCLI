#!/bin/sh
set -e

echo "==> Worker waiting for database..."
python - <<'PY'
import os, sys, time
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django
django.setup()
from django.db import connection
for i in range(90):
    try:
        connection.ensure_connection()
        print("Database ready.")
        break
    except Exception as e:
        if i == 0:
            print(f"DB not ready ({e}); retrying...")
        time.sleep(1)
else:
    print("Database not available after 90s.")
    sys.exit(1)
PY

echo "==> Start worker: $@"
exec "$@"
