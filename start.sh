#!/bin/sh
set -eu

HOST="0.0.0.0"
PORT="${PORT:-10000}"

exec python -m genesis.api --host "$HOST" --port "$PORT"
