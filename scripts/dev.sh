#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export DATABASE_URL="${DATABASE_URL:-postgresql://studentos:studentos@127.0.0.1:54329/studentos}"
export API_INTERNAL_URL="${API_INTERNAL_URL:-http://127.0.0.1:43124}"
export PYTHONPATH="$ROOT"

if ! "$ROOT/.venv/bin/python" -c "import psycopg2, fastapi" 2>/dev/null; then
  python3 -m venv "$ROOT/.venv"
  "$ROOT/.venv/bin/pip" install -r "$ROOT/api/requirements.txt"
fi

"$ROOT/.venv/bin/python" "$ROOT/pipeline/ingest.py" --dsn "$DATABASE_URL"

"$ROOT/.venv/bin/uvicorn" api.app.main:app --host 0.0.0.0 --port 43124 &
API_PID=$!
trap 'kill $API_PID 2>/dev/null || true' EXIT

cd "$ROOT/web"
if [ ! -d node_modules ]; then
  npm install
fi
npm run dev
