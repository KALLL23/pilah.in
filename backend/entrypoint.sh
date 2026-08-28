#!/bin/sh
set -eu

alembic -c alembic.ini upgrade head
python -m app.scripts.bootstrap_admin
exec uvicorn app.main:app --host "${APP_HOST:-0.0.0.0}" --port "${APP_PORT:-8000}"
