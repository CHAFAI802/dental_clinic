#!/bin/sh
set -e

python <<'EOF'
import os
import socket
import sys
import time

host = os.environ.get("POSTGRES_HOST", "db")
port = int(os.environ.get("POSTGRES_PORT", "5432"))

for _ in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            break
    except OSError:
        time.sleep(1)
else:
    sys.exit("PostgreSQL is unavailable.")
EOF

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
