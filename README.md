# Haryana Roadways — Digital Passenger Platform

A full-stack government-grade platform for Haryana Roadways: OTP authentication, live bus tracking, digital ticketing, and bus pass management.

## Project Structure

```
haryana_roadways/
├── backend/     FastAPI + PostgreSQL + Redis
├── admin/       React admin panel (Vite)
└── mobile/      Flutter passenger app
```

## Quick Start (Development)

### 1. Backend

```bash
cd backend
cp .env.example .env          # demo credentials pre-filled
docker compose up -d            # PostgreSQL + Redis
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

**Dev login:**
- Any mobile + OTP `123456`
- Admin: `9999999999` + OTP `123456`

### 2. Admin Panel

```bash
cd admin
npm install
npm run dev                     # http://localhost:5173
```

Login with admin mobile `9999999999` and OTP `123456`.

### 3. Mobile App

```bash
cd mobile
flutter pub get
flutter run                     # Android emulator / device
```

Uses `http://localhost:8000` by default (see `lib/core/config.dart`).

## Running Tests

```bash
# Backend (requires PostgreSQL + Redis running)
cd backend && uv run pytest tests/ -v

# Mobile
cd mobile && flutter test

# Admin build check
cd admin && npm run build
```

## Production

Copy `.env.example` and set `DEBUG=False` with real credentials:

- `SECRET_KEY` — long random string
- `POSTGRES_PASSWORD` — strong password
- `OTP_DEV_MODE=False` + `SMS_API_KEY`
- `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET`
- `BUS_TRACKING_API_KEY`
- Unset `SEED_ADMIN_MOBILE`

## Features

| Feature | Backend | Admin | Mobile |
|---------|---------|-------|--------|
| OTP Auth | ✅ | ✅ | ✅ |
| Live Bus Tracking | ✅ | ✅ | ✅ |
| Digital Ticketing | ✅ | ✅ | ✅ |
| Bus Pass Management | ✅ | ✅ | ✅ |
| Admin Dashboard | ✅ | ✅ | — |
| Aadhaar KYC | Stub | — | Stub |
| Razorpay Payments | Demo/Live | — | Demo |
