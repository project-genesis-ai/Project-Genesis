#!/bin/sh
set -eu

HOST="0.0.0.0"
PORT="${PORT:-10000}"

if [ -n "${DATABASE_URL:-}" ]; then
  python -m alembic upgrade head
fi

exec python -m genesis.api --host "$HOST" --port "$PORT"
