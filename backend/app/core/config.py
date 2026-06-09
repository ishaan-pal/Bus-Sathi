from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, field_validator
from typing import List, Optional
import secrets


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "Haryana Roadways API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = secrets.token_urlsafe(32)
    API_V1_STR: str = "/api/v1"

    # ── JWT ──────────────────────────────────────────────
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24        # 1 day
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    # ── Database ─────────────────────────────────────────
    DATABASE_URL: str = "postgresql://haryana:haryana123@localhost:5432/haryana_roadways"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # ── Redis ────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    OTP_EXPIRE_SECONDS: int = 300                     # 5 minutes
    TICKET_CACHE_SECONDS: int = 3600                  # 1 hour

    # ── OTP ──────────────────────────────────────────────
    OTP_LENGTH: int = 6
    OTP_MAX_ATTEMPTS: int = 3
    OTP_DEV_MODE: bool = True                         # skips real SMS in dev
    OTP_DEV_FIXED: str = "123456"                     # fixed OTP in dev mode

    # ── SMS (Fast2SMS — free tier) ────────────────────────
    SMS_API_KEY: Optional[str] = None
    SMS_SENDER_ID: str = "HRRDWY"

    # ── Aadhaar (stub for now) ────────────────────────────
    AADHAAR_ENABLED: bool = False
    AADHAAR_API_URL: Optional[str] = None
    AADHAAR_API_KEY: Optional[str] = None

    # ── Razorpay (sandbox) ───────────────────────────────
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None
    RAZORPAY_CURRENCY: str = "INR"

    # ── CORS ─────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # ── File Upload ──────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 5
    UPLOAD_DIR: str = "uploads"
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp"]

    # ── Fare Engine ──────────────────────────────────────
    FARE_BASE_PAISE_PER_KM: int = 85          # ₹0.85/km ordinary
    FARE_MIN_PAISE: int = 1000                # ₹10 minimum fare
    CHILD_FARE_PERCENT: int = 50              # 50% for children under 12
    SENIOR_FARE_PERCENT: int = 50             # 50% for senior citizens
    STUDENT_FARE_PERCENT: int = 50            # 50% for students with pass

    # ── Bus Tracking ─────────────────────────────────────
    BUS_LOCATION_STALE_SECONDS: int = 120     # mark stale after 2 min
    TRACKING_POLL_INTERVAL_SECONDS: int = 15

    # ── Security ─────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60
    BCRYPT_ROUNDS: int = 12

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


settings = Settings()