#!/usr/bin/env python3
"""Add extra test buses with GPS. Safe to run multiple times."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import AsyncSessionLocal
from app.db.init_db import seed_extra_test_buses


async def main() -> None:
    async with AsyncSessionLocal() as db:
        await seed_extra_test_buses(db)
    print("Done. Restart the app search to see buses.")


if __name__ == "__main__":
    asyncio.run(main())
