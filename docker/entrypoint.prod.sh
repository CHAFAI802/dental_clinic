#!/bin/sh
set -eu

python <<'PY'
import os
import socket
import sys
import time

host = os.environ.get("POSTGRES_HOST", "db")
port = int(os.environ.get("POSTGRES_PORT", "5432"))

for attempt in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            print("PostgreSQL is available.")
            break
    except OSError:
        time.sleep(1)
else:
    sys.exit("PostgreSQL is unavailable after 60 attempts.")
PY

exec "$@"
