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


# ── Seed test network route (15 stations for mobile search testing) ─────────────
async def seed_test_network_route(db: AsyncSession) -> None:
    from sqlalchemy import select

    result = await db.execute(
        select(Route).where(Route.route_number == "HR-06")
    )
    if result.scalar_one_or_none():
        print("⏭️  Test network route HR-06 already exists, skipping")
        return

    # 15 major Haryana stations on one route so any pair can be searched in dev.
    test_stops = [
        ("Chandigarh ISBT", 0, 0.0, 30.7333, 76.7794, 0),
        ("Panchkula", 1, 8.0, 30.6942, 76.8508, 15),
        ("Ambala City", 2, 48.0, 30.3782, 76.7767, 75),
        ("Karnal Bus Stand", 3, 95.0, 29.6857, 76.9905, 130),
        ("Panipat", 4, 123.0, 29.3909, 76.9635, 165),
        ("Sonipat", 5, 155.0, 28.9931, 77.0151, 200),
        ("Rohtak Bus Stand", 6, 195.0, 28.8955, 76.6066, 250),
        ("Hisar Bus Stand", 7, 260.0, 29.1492, 75.7217, 330),
        ("Bhiwani", 8, 290.0, 28.7930, 76.1390, 370),
        ("Gurugram Bus Stand", 9, 340.0, 28.4595, 77.0266, 430),
        ("Faridabad", 10, 365.0, 28.4089, 77.3178, 460),
        ("Kurukshetra Bus Stand", 11, 420.0, 29.9695, 76.8783, 530),
        ("Yamunanagar Bus Stand", 12, 450.0, 30.1290, 77.2674, 565),
        ("Sirsa", 13, 520.0, 29.5349, 75.0289, 650),
        ("Rewari", 14, 560.0, 28.1990, 76.6198, 700),
    ]

    route_id = str(uuid.uuid4())
    route = Route(
        id=route_id,
        route_number="HR-06",
        name="Haryana State Network (Test)",
        origin="Chandigarh",
        destination="Rewari",
        total_distance_km=560.0,
        estimated_duration_minutes=700,
        is_active=True,
    )
    db.add(route)

    for stop_name, order, dist, lat, lng, mins in test_stops:
        db.add(
            RouteStop(
                id=str(uuid.uuid4()),
                route_id=route_id,
                stop_name=stop_name,
                stop_order=order,
                distance_from_origin_km=dist,
                latitude=lat,
                longitude=lng,
                scheduled_minutes_from_origin=mins,
                is_major_stop=True,
            )
        )

    await db.commit()
    print(f"✅ Seeded test route HR-06 with {len(test_stops)} stations")


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


# ── Extra test buses (idempotent — safe to re-run) ────────────────────────────
async def seed_extra_test_buses(db: AsyncSession) -> None:
    """
    Add more running buses with live GPS for mobile search & tracking tests.
    Especially on HR-06 where stations exist but no buses were assigned.
    """
    from sqlalchemy import select
    from datetime import datetime, timezone

    result = await db.execute(select(Route.id, Route.route_number))
    route_map = {rn: rid for rid, rn in result.fetchall()}

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # bus_number, reg, type, route, lat, lng, status, driver, conductor, mobile,
    # current_stop, next_stop, delay
    extra_buses = [
        ("HR-29-2001", "HR29PA2001", BusType.EXPRESS,    "HR-06", 30.7100, 76.8150, BusStatus.RUNNING, "Vikram Singh",  "Rohit Mehta",   "9812345801", "Panchkula",       "Ambala City",       0),
        ("HR-29-2002", "HR29PA2002", BusType.ORDINARY,   "HR-06", 30.4200, 76.7800, BusStatus.RUNNING, "Sunil Hooda",   "Ajay Punia",    "9812345802", "Ambala City",     "Karnal Bus Stand",  0),
        ("HR-29-2003", "HR29PA2003", BusType.ORDINARY,   "HR-06", 29.7200, 76.9800, BusStatus.RUNNING, "Manoj Yadav",   "Kuldeep Singh", "9812345803", "Karnal Bus Stand","Panipat",           0),
        ("HR-29-2004", "HR29PA2004", BusType.ORDINARY,   "HR-06", 29.3500, 76.9600, BusStatus.DELAYED, "Harish Kumar",  "Nitin Sharma",  "9812345804", "Panipat",         "Sonipat",           12),
        ("HR-29-2005", "HR29PA2005", BusType.EXPRESS,    "HR-06", 28.9800, 77.0000, BusStatus.RUNNING, "Pradeep Rana",  "Sandeep Ahlawat","9812345805", "Sonipat",        "Rohtak Bus Stand",  0),
        ("HR-29-2006", "HR29PA2006", BusType.ORDINARY,   "HR-06", 28.4700, 77.0300, BusStatus.RUNNING, "Gaurav Bhatia", "Anil Chaudhary","9812345806", "Gurugram Bus Stand","Faridabad",       0),
        ("HR-29-2007", "HR29PA2007", BusType.EXPRESS,    "HR-01", 30.6200, 76.8300, BusStatus.RUNNING, "Balbir Singh",  "Joginder Pal",  "9812345807", "Zirakpur",        "Derabassi",         0),
        ("HR-29-2008", "HR29PA2008", BusType.ORDINARY,   "HR-01", 30.4800, 76.7900, BusStatus.RUNNING, "Charanjit Singh","Gurmeet Singh","9812345808", "Rajpura",         "Ambala Cantonment", 5),
        ("HR-29-2009", "HR29PA2009", BusType.ORDINARY,   "HR-04", 28.4900, 77.0800, BusStatus.RUNNING, "Yogesh Kumar",  "Hemant Jain",   "9812345809", "Iffco Chowk",     "Rajiv Chowk Metro", 0),
        ("HR-29-2010", "HR29PA2010", BusType.SUPER_EXPRESS,"HR-06",30.2500, 76.8700, BusStatus.RUNNING,"Rakesh Dahiya", "Sombir Malik",  "9812345810", "Hisar Bus Stand", "Bhiwani",           0),
    ]

    added = 0
    for row in extra_buses:
        (bus_num, reg, btype, route_num, lat, lng, status, driver, conductor,
         cond_mobile, current_stop, next_stop, delay) = row

        existing = await db.execute(
            select(Bus).where(Bus.bus_number == bus_num)
        )
        if existing.scalar_one_or_none():
            continue

        bus = Bus(
            id=str(uuid.uuid4()),
            bus_number=bus_num,
            registration_number=reg,
            bus_type=btype,
            route_id=route_map.get(route_num),
            current_latitude=lat,
            current_longitude=lng,
            last_location_update=now,
            status=status,
            is_active=True,
            driver_name=driver,
            conductor_name=conductor,
            conductor_mobile=cond_mobile,
            current_stop=current_stop,
            next_stop=next_stop,
            delay_minutes=delay,
            seating_capacity=52,
            standing_capacity=20,
        )
        db.add(bus)
        added += 1

    # Promote depot bus on HR-01 so Chandigarh–Ambala searches return more results
    depot = await db.execute(
        select(Bus).where(Bus.bus_number == "HR-29-1006")
    )
    depot_bus = depot.scalar_one_or_none()
    if depot_bus and depot_bus.status == BusStatus.DEPOT:
        depot_bus.status = BusStatus.RUNNING
        depot_bus.current_latitude = 30.6500
        depot_bus.current_longitude = 76.8200
        depot_bus.last_location_update = now
        depot_bus.current_stop = "Zirakpur"
        depot_bus.next_stop = "Derabassi"
        depot_bus.delay_minutes = 0

    await db.commit()
    if added:
        print(f"✅ Added {added} extra test buses with live GPS")
    else:
        print("⏭️  Extra test buses already present")


# ── Main entrypoint ───────────────────────────────────────────────────────────
async def init_db() -> None:
    await create_tables()
    async with AsyncSessionLocal() as db:
        await seed_admin(db)
        await seed_routes(db)
        await seed_test_network_route(db)
        await seed_buses(db)
        await seed_extra_test_buses(db)
    print("🚌 Haryana Roadways DB initialized successfully")


if __name__ == "__main__":
    asyncio.run(init_db())