import asyncio
import uuid
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine, AsyncSessionLocal
from app.models.user import User
from app.models.route import Route, RouteStop
from app.models.bus import Bus, BusType, BusStatus
from app.models.ticket import Ticket
from app.models.pass_ import BusPass


# ── Create all tables ─────────────────────────────────────────────────────────
async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables created successfully")


# ── Seed admin user ───────────────────────────────────────────────────────────
async def seed_admin(db: AsyncSession) -> None:
    if not settings.SEED_ADMIN_MOBILE:
        print("⏭️  SEED_ADMIN_MOBILE not set, skipping admin seed")
        return

    from sqlalchemy import select
    result = await db.execute(
        select(User).where(User.mobile == settings.SEED_ADMIN_MOBILE)
    )
    if result.scalar_one_or_none():
        print("⏭️  Admin already exists, skipping")
        return

    admin = User(
        id=str(uuid.uuid4()),
        mobile=settings.SEED_ADMIN_MOBILE,
        name="Admin User",
        date_of_birth="1985-01-01",
        aadhaar_verified=True,
        profile_complete=True,
        is_active=True,
        is_admin=True,
        is_staff=True,
    )
    db.add(admin)
    await db.commit()
    print(f"✅ Admin user seeded  →  mobile: {settings.SEED_ADMIN_MOBILE}")


# ── Seed Haryana routes ───────────────────────────────────────────────────────
async def seed_routes(db: AsyncSession) -> None:
    from sqlalchemy import select
    result = await db.execute(select(Route).limit(1))
    if result.scalar_one_or_none():
        print("⏭️  Routes already seeded, skipping")
        return

    routes_data = [
        {
            "route_number": "HR-01",
            "name": "Chandigarh – Ambala Express",
            "origin": "Chandigarh",
            "destination": "Ambala",
            "total_distance_km": 48.0,
            "estimated_duration_minutes": 75,
            "stops": [
                ("Chandigarh ISBT", 0, 0.0, 30.7333, 76.7794, 0),
                ("Zirakpur", 1, 12.0, 30.6480, 76.8178, 18),
                ("Derabassi", 2, 18.0, 30.5960, 76.8330, 28),
                ("Rajpura", 3, 28.0, 30.4820, 76.5960, 42),
                ("Ambala Cantonment", 4, 42.0, 30.3520, 76.8280, 65),
                ("Ambala City", 5, 48.0, 30.3782, 76.7767, 75),
            ],
        },
        {
            "route_number": "HR-02",
            "name": "Karnal – Ambala Ordinary",
            "origin": "Karnal",
            "destination": "Ambala",
            "total_distance_km": 62.0,
            "estimated_duration_minutes": 90,
            "stops": [
                ("Karnal Bus Stand", 0, 0.0, 29.6857, 76.9905, 0),
                ("Gharaunda", 1, 14.0, 29.5380, 76.9750, 22),
                ("Panipat", 2, 28.0, 29.3909, 76.9635, 42),
                ("Samalkha", 3, 40.0, 29.2340, 76.9500, 60),
                ("Ambala City", 4, 62.0, 30.3782, 76.7767, 90),
            ],
        },
        {
            "route_number": "HR-03",
            "name": "Hisar – Rohtak Express",
            "origin": "Hisar",
            "destination": "Rohtak",
            "total_distance_km": 95.0,
            "estimated_duration_minutes": 120,
            "stops": [
                ("Hisar Bus Stand", 0, 0.0, 29.1492, 75.7217, 0),
                ("Hansi", 1, 22.0, 29.1020, 75.9680, 30),
                ("Bhiwani", 2, 50.0, 28.7930, 76.1390, 65),
                ("Jhajjar", 3, 78.0, 28.6080, 76.6560, 100),
                ("Rohtak Bus Stand", 4, 95.0, 28.8955, 76.6066, 120),
            ],
        },
        {
            "route_number": "HR-04",
            "name": "Gurugram – Delhi Ordinary",
            "origin": "Gurugram",
            "destination": "Delhi",
            "total_distance_km": 32.0,
            "estimated_duration_minutes": 60,
            "stops": [
                ("Gurugram Bus Stand", 0, 0.0, 28.4595, 77.0266, 0),
                ("Iffco Chowk", 1, 5.0, 28.4726, 77.0730, 10),
                ("Rajiv Chowk Metro", 2, 15.0, 28.5355, 77.1390, 25),
                ("Dhaula Kuan", 3, 25.0, 28.5921, 77.1580, 45),
                ("Delhi ISBT Kashmere Gate", 4, 32.0, 28.6677, 77.2270, 60),
            ],
        },
        {
            "route_number": "HR-05",
            "name": "Yamunanagar – Kurukshetra Ordinary",
            "origin": "Yamunanagar",
            "destination": "Kurukshetra",
            "total_distance_km": 55.0,
            "estimated_duration_minutes": 80,
            "stops": [
                ("Yamunanagar Bus Stand", 0, 0.0, 30.1290, 77.2674, 0),
                ("Jagadhri", 1, 5.0, 30.1640, 77.3030, 10),
                ("Radaur", 2, 18.0, 30.0560, 77.2180, 28),
                ("Shahabad", 3, 32.0, 30.1680, 76.9100, 48),
                ("Kurukshetra Bus Stand", 4, 55.0, 29.9695, 76.8783, 80),
            ],
        },
    ]

    for r in routes_data:
        route_id = str(uuid.uuid4())
        route = Route(
            id=route_id,
            route_number=r["route_number"],
            name=r["name"],
            origin=r["origin"],
            destination=r["destination"],
            total_distance_km=r["total_distance_km"],
            estimated_duration_minutes=r["estimated_duration_minutes"],
            is_active=True,
        )
        db.add(route)

        for stop_name, order, dist, lat, lng, mins in r["stops"]:
            stop = RouteStop(
                id=str(uuid.uuid4()),
                route_id=route_id,
                stop_name=stop_name,
                stop_order=order,
                distance_from_origin_km=dist,
                latitude=lat,
                longitude=lng,
                scheduled_minutes_from_origin=mins,
                is_major_stop=(order == 0 or order == len(r["stops"]) - 1),
            )
            db.add(stop)

    await db.commit()
    print(f"✅ Seeded {len(routes_data)} routes with stops")


# ── Seed sample buses ─────────────────────────────────────────────────────────
async def seed_buses(db: AsyncSession) -> None:
    from sqlalchemy import select
    result = await db.execute(select(Bus).limit(1))
    if result.scalar_one_or_none():
        print("⏭️  Buses already seeded, skipping")
        return

    # Fetch route IDs
    result = await db.execute(select(Route.id, Route.route_number))
    route_map = {rn: rid for rid, rn in result.fetchall()}

    buses_data = [
        ("HR-29-1001", "HR29PA1001", BusType.EXPRESS,    "HR-01", 29.9500, 76.9000, BusStatus.RUNNING,  "Rajesh Kumar",  "Suresh Singh",  "9812345671"),
        ("HR-29-1002", "HR29PA1002", BusType.ORDINARY,   "HR-02", 29.5000, 76.9500, BusStatus.RUNNING,  "Amit Sharma",   "Vikram Das",    "9812345672"),
        ("HR-29-1003", "HR29PA1003", BusType.ORDINARY,   "HR-03", 29.0000, 76.0000, BusStatus.DELAYED,  "Ravi Verma",    "Deepak Nain",   "9812345673"),
        ("HR-29-1004", "HR29PA1004", BusType.ORDINARY,   "HR-04", 28.5000, 77.0500, BusStatus.RUNNING,  "Sanjay Yadav",  "Mohit Hooda",   "9812345674"),
        ("HR-29-1005", "HR29PA1005", BusType.ORDINARY,   "HR-05", 30.0500, 77.1000, BusStatus.RUNNING,  "Naresh Kumar",  "Pawan Kalyan",  "9812345675"),
        ("HR-29-1006", "HR29PA1006", BusType.MINI,       "HR-01", None,    None,    BusStatus.DEPOT,    "Dinesh Saini",  "Ramesh Gupta",  "9812345676"),
    ]

    for bus_num, reg, btype, route_num, lat, lng, status, driver, conductor, cond_mobile in buses_data:
        from datetime import datetime, timezone
        bus = Bus(
            id=str(uuid.uuid4()),
            bus_number=bus_num,
            registration_number=reg,
            bus_type=btype,
            route_id=route_map.get(route_num),
            current_latitude=lat,
            current_longitude=lng,
            last_location_update=datetime.now(timezone.utc).replace(tzinfo=None) if lat else None,
            status=status,
            is_active=True,
            driver_name=driver,
            conductor_name=conductor,
            conductor_mobile=cond_mobile,
            delay_minutes=10 if status == BusStatus.DELAYED else 0,
            seating_capacity=52,
            standing_capacity=20,
        )
        db.add(bus)

    await db.commit()
    print(f"✅ Seeded {len(buses_data)} buses")


# ── Main entrypoint ───────────────────────────────────────────────────────────
async def init_db() -> None:
    await create_tables()
    async with AsyncSessionLocal() as db:
        await seed_admin(db)
        await seed_routes(db)
        await seed_buses(db)
    print("🚌 Haryana Roadways DB initialized successfully")


if __name__ == "__main__":
    asyncio.run(init_db())