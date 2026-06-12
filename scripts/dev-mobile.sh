#!/usr/bin/env bash
# Run the Flutter app on a USB-connected Android device with reliable API access.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/mobile"

"$ROOT/scripts/setup-adb.sh"

echo ""
echo "Starting app (API -> http://127.0.0.1:8000/api/v1)"
echo "Ensure backend is running:"
echo "  cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""

exec flutter run --dart-define=API_HOST=127.0.0.1 "$@"
