from pydantic import model_validator
from pydantic_settings import BaseSettings
from typing import List, Optional
import secrets
import warnings


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "Haryana Roadways API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: Optional[str] = None
    API_V1_STR: str = "/api/v1"

    # ── JWT ──────────────────────────────────────────────
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24        # 1 day
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    # ── Database ─────────────────────────────────────────
    # Set DATABASE_URL directly, or provide POSTGRES_* (used by docker-compose too)
    DATABASE_URL: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: Optional[str] = None
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # ── Redis ────────────────────────────────────────────
    REDIS_URL: Optional[str] = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    TICKET_CACHE_SECONDS: int = 3600                  # 1 hour

    # ── Aadhaar (stub until govt API credentials obtained) ─
    AADHAAR_ENABLED: bool = False
    AADHAAR_API_URL: Optional[str] = None
    AADHAAR_API_KEY: Optional[str] = None

    # ── Razorpay ─────────────────────────────────────────
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None
    RAZORPAY_CURRENCY: str = "INR"

    # ── Bus GPS / ETM device feed ────────────────────────
    BUS_TRACKING_API_KEY: Optional[str] = None

    # ── DB seeding (dev only — leave unset in production) ─
    SEED_ADMIN_MOBILE: Optional[str] = None

    # ── CORS (comma-separated in .env) ─────────────────
    ALLOWED_ORIGINS: str = ""

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

    @property
    def cors_origins(self) -> List[str]:
        if not self.ALLOWED_ORIGINS.strip():
            return []
        return [
            origin.strip()
            for origin in self.ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]

    @model_validator(mode="after")
    def assemble_connection_urls(self) -> "Settings":
        if not self.DATABASE_URL:
            if self.POSTGRES_USER and self.POSTGRES_PASSWORD and self.POSTGRES_DB:
                object.__setattr__(
                    self,
                    "DATABASE_URL",
                    (
                        f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                        f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
                    ),
                )
            else:
                raise ValueError(
                    "DATABASE_URL or POSTGRES_USER, POSTGRES_PASSWORD, and "
                    "POSTGRES_DB must be set. Copy .env.example to .env."
                )

        if not self.REDIS_URL:
            if self.REDIS_PASSWORD:
                url = (
                    f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:"
                    f"{self.REDIS_PORT}/{self.REDIS_DB}"
                )
            else:
                url = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
            object.__setattr__(self, "REDIS_URL", url)

        return self

    @model_validator(mode="after")
    def validate_secrets(self) -> "Settings":
        if not self.SECRET_KEY:
            if self.DEBUG:
                object.__setattr__(self, "SECRET_KEY", secrets.token_urlsafe(32))
                warnings.warn(
                    "SECRET_KEY not set — using an ephemeral key. "
                    "Set SECRET_KEY in .env for stable sessions.",
                    stacklevel=2,
                )
            else:
                raise ValueError("SECRET_KEY must be set when DEBUG=False")

        if not self.DEBUG and not self.BUS_TRACKING_API_KEY:
            warnings.warn(
                "BUS_TRACKING_API_KEY not set — rely on per-depot tracking keys "
                "in the tracking_api_keys table for production GPS feeds.",
                stacklevel=2,
            )

        return self

    @property
    def payment_demo_mode(self) -> bool:
        """True when Razorpay credentials are not configured."""
        return not (self.RAZORPAY_KEY_ID and self.RAZORPAY_KEY_SECRET)


settings = Settings()
