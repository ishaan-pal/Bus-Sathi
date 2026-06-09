from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool
from app.core.config import settings

# ── Convert sync postgres URL to async ───────────────────────────────────────
def _make_async_url(url: str) -> str:
    """
    SQLAlchemy async requires postgresql+asyncpg://
    Convert from standard postgresql:// if needed.
    """
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


ASYNC_DATABASE_URL = _make_async_url(settings.DATABASE_URL)

# ── Engine ────────────────────────────────────────────────────────────────────
engine: AsyncEngine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=settings.DEBUG,                  # log SQL in debug mode
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,                   # test connections before using
    pool_recycle=3600,                    # recycle connections every hour
)

# ── Session Factory ───────────────────────────────────────────────────────────
AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,               # keep objects usable after commit
    autocommit=False,
    autoflush=False,
)