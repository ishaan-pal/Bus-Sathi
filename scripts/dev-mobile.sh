#!/usr/bin/env bash
# Run the Flutter app on a USB-connected Android device with reliable API access.
# Uses adb reverse so the phone reaches the WSL backend via localhost (no Wi‑Fi / port-proxy needed).
set -euo pipefail

cd "$(dirname "$0")/../mobile"

if ! adb devices | grep -q 'device$'; then
  echo "No Android device found. Connect via USB and enable USB debugging."
  exit 1
fi

adb reverse tcp:8000 tcp:8000
echo "adb reverse active: phone localhost:8000 -> PC localhost:8000"
echo ""

exec flutter run --dart-define=API_HOST=127.0.0.1 "$@"
