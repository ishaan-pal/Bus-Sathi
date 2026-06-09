import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.v1.router import api_router
from app.db.init_db import init_db


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events.
    - Creates DB tables and seeds initial data on first run
    - Ensures upload directories exist
    """
    print("🚌 Starting Haryana Roadways API...")

    # Create upload directories
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "passes"), exist_ok=True)

    # Initialize database
    try:
        await init_db()
    except Exception as e:
        print(f"⚠️  DB init warning: {e}")
        print("   Make sure PostgreSQL is running and .env is configured")

    print(f"✅ API ready at http://localhost:8000")
    print(f"📖 Docs at http://localhost:8000/docs")

    yield

    print("🛑 Shutting down Haryana Roadways API...")


# ── App Instance ──────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## Haryana Roadways Passenger App — Backend API

A modern government-grade passenger platform for Haryana Roadways.

### Features
- 🔐 **OTP Authentication** — Mobile OTP with JWT tokens
- 🗺️ **Live Bus Tracking** — Real-time GPS location & ETA
- 🎫 **Digital Ticketing** — Route-based fare with age concessions
- 🪪 **Bus Pass Management** — Student, senior citizen, monthly passes
- 🛡️ **Secure Verification** — Rotating tokens for conductor checks

### Auth
All protected endpoints require `Authorization: Bearer <token>` header.
Use `/api/v1/auth/send-otp` → `/api/v1/auth/verify-otp` to get tokens.

### Demo Credentials
- **Any mobile number** + OTP `123456` (dev mode)
- **Admin**: mobile `9999999999` + OTP `123456`
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Security Headers Middleware ───────────────────────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store"
    return response


# ── Rate Limiting Middleware ──────────────────────────────────────────────────
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """
    Simple Redis-based rate limiting.
    Skipped if Redis is unavailable (dev fallback).
    """
    try:
        from app.core.dependencies import get_redis
        redis = await get_redis()

        client_ip = request.client.host
        key = f"rate:{client_ip}"
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, 60)

        if count > settings.RATE_LIMIT_PER_MINUTE:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Too many requests. Please slow down.",
                    "retry_after": 60,
                },
            )
    except Exception:
        # Redis unavailable — skip rate limiting in dev
        pass

    return await call_next(request)


# ── Global Exception Handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all for unhandled exceptions — never expose stack traces."""
    print(f"Unhandled error on {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred"},
    )


# ── Static Files (uploaded documents) ────────────────────────────────────────
if os.path.exists(settings.UPLOAD_DIR):
    app.mount(
        "/uploads",
        StaticFiles(directory=settings.UPLOAD_DIR),
        name="uploads",
    )


# ── API Router ────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix=settings.API_V1_STR)


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for load balancer / uptime monitoring."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint — redirects to docs."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }