#!/usr/bin/env bash
# Forward phone localhost:8000 -> PC localhost:8000 (required for physical Android dev).
set -euo pipefail

if ! command -v adb >/dev/null 2>&1; then
  echo "adb not found. Install Android platform-tools."
  exit 1
fi

if ! adb devices | grep -q 'device$'; then
  echo "No Android device found. Connect via USB and enable USB debugging."
  exit 1
fi

adb reverse tcp:8000 tcp:8000
echo "✓ adb reverse active (phone 127.0.0.1:8000 -> PC localhost:8000)"
