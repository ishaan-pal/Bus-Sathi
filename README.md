# Haryana Roadways — Digital Passenger Platform

Full-stack platform for Haryana Roadways: mobile login (no OTP), Aadhaar KYC, live bus tracking, digital ticketing, and bus pass management.

## Project Structure

```
haryana_roadways/
├── backend/     FastAPI + PostgreSQL + Redis
├── admin/       React admin panel (Vite)
└── mobile/      Flutter passenger app (Android/iOS)
```

## Quick Start

### 1. Backend

```bash
cd backend
cp .env.example .env
docker compose up -d
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

**Re-seed test buses** (adds GPS-tracked buses on all routes):

```bash
cd backend && uv run python scripts/seed_test_buses.py
```

### 2. Mobile (Android)

**USB-connected phone (recommended on WSL2):**

```bash
chmod +x scripts/dev-mobile.sh
./scripts/dev-mobile.sh
```

This runs `adb reverse` so the phone uses `127.0.0.1:8000` — no Wi‑Fi or port-proxy setup needed.

**Wi‑Fi phone (WSL2):** In **PowerShell as Administrator**:

```powershell
.\scripts\forward-api-port.ps1
```

Then use the printed LAN IP. Re-run after a WSL restart.

```bash
cd mobile
flutter pub get

# Wi‑Fi phone (same network as PC):
flutter run --dart-define=API_HOST=192.168.x.x

# Android emulator:
flutter run

# Build APK for phone:
flutter build apk --debug --dart-define=API_HOST=192.168.x.x
adb install build/app/outputs/flutter-apk/app-debug.apk
```

**Login:** enter any 10-digit mobile → instant access (no OTP).

**Aadhaar:** required for booking tickets & applying for passes (stub: any 12-digit number until govt API is connected).

### 3. Admin Panel

```bash
cd admin && npm install && npm run dev
```

Sign in with admin mobile from `.env` (`SEED_ADMIN_MOBILE`, default `9999999999`) — no OTP.

## Auth Flow

| Step | Mobile App | Admin |
|------|------------|-------|
| Sign in | `POST /auth/login` {mobile} | Same |
| Browse buses | ✓ after login | — |
| Book ticket / apply pass | Requires Aadhaar verify | — |
| Admin features | — | Requires `is_admin` |

## Tests

```bash
cd backend && uv run pytest tests/ -v
cd mobile && flutter test
cd admin && npm run build
```

## Production Checklist

Set in `.env` with `DEBUG=False`:

- `SECRET_KEY` — long random string
- `POSTGRES_PASSWORD` — strong password
- `BUS_TRACKING_API_KEY` — GPS device feed
- `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` — live payments
- `AADHAAR_API_URL` / `AADHAAR_API_KEY` — when govt credentials obtained
- Unset `SEED_ADMIN_MOBILE`
