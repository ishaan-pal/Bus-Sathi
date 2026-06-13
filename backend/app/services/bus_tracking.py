import json
from datetime import datetime, timezone
from typing import Optional

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.config import settings
from app.models.bus import Bus, BusStatus
from app.models.route import Route, RouteStop


# ── Redis Key Helpers ─────────────────────────────────────────────────────────
def _bus_location_key(bus_id: str) -> str:
    return f"bus:location:{bus_id}"

def _route_buses_key(route_id: str) -> str:
    return f"route:buses:{route_id}"

def _bus_eta_key(bus_id: str, stop_name: str) -> str:
    return f"bus:eta:{bus_id}:{stop_name.lower().replace(' ', '_')}"


# ── Update Bus Location ───────────────────────────────────────────────────────
async def update_bus_location(
    bus_id: str,
    latitude: float,
    longitude: float,
    speed_kmh: Optional[float],
    heading: Optional[float],
    redis: aioredis.Redis,
    db: AsyncSession,
    bus: Optional[Bus] = None,
) -> bool:
    """
    Called by GPS device / ETM feed to update bus position.
    Persists to DB and caches in Redis for fast reads.
    """
    if bus is None:
        result = await db.execute(select(Bus).where(Bus.id == bus_id))
        bus = result.scalar_one_or_none()
    if not bus:
        return False

    bus_id = bus.id
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # Update DB
    bus.current_latitude = latitude
    bus.current_longitude = longitude
    bus.last_location_update = now
    if speed_kmh is not None:
        bus.current_speed_kmh = speed_kmh
    if heading is not None:
        bus.heading_degrees = heading
    if bus.status == BusStatus.DEPOT:
        bus.status = BusStatus.RUNNING

    await db.commit()

    # Cache in Redis for fast reads (TTL = stale threshold + buffer)
    cache_data = {
        "bus_id": bus_id,
        "bus_number": bus.bus_number,
        "latitude": latitude,
        "longitude": longitude,
        "speed_kmh": speed_kmh,
        "heading": heading,
        "status": bus.status.value,
        "delay_minutes": bus.delay_minutes,
        "current_stop": bus.current_stop,
        "next_stop": bus.next_stop,
        "last_updated": now.isoformat(),
        "is_stale": False,
    }
    await redis.setex(
        _bus_location_key(bus_id),
        settings.BUS_LOCATION_STALE_SECONDS + 60,
        json.dumps(cache_data),
    )

    return True


# ── Get Bus Location ──────────────────────────────────────────────────────────
async def get_bus_location(
    bus_id: str,
    redis: aioredis.Redis,
    db: AsyncSession,
) -> Optional[dict]:
    """
    Returns latest bus location. Tries Redis cache first,
    falls back to DB if cache miss.
    """
    # Try cache first
    cached = await redis.get(_bus_location_key(bus_id))
    if cached:
        data = json.loads(cached)
        # Mark stale if last update is old
        last_updated = datetime.fromisoformat(data["last_updated"])
        delta = (datetime.now(timezone.utc) - last_updated).total_seconds()
        data["is_stale"] = delta > settings.BUS_LOCATION_STALE_SECONDS
        return data

    # Cache miss — fetch from DB
    result = await db.execute(select(Bus).where(Bus.id == bus_id))
    bus = result.scalar_one_or_none()
    if not bus or not bus.current_latitude:
        return None

    return {
        "bus_id": bus_id,
        "bus_number": bus.bus_number,
        "latitude": bus.current_latitude,
        "longitude": bus.current_longitude,
        "speed_kmh": bus.current_speed_kmh,
        "heading": bus.heading_degrees,
        "status": bus.status.value,
        "delay_minutes": bus.delay_minutes,
        "current_stop": bus.current_stop,
        "next_stop": bus.next_stop,
        "last_updated": (
            bus.last_location_update.isoformat()
            if bus.last_location_update else None
        ),
        "is_stale": bus.is_location_stale,
    }


# ── Calculate ETA ─────────────────────────────────────────────────────────────
async def calculate_eta(
    bus: Bus,
    target_stop_name: str,
    route_stops: list[RouteStop],
) -> Optional[dict]:
    """
    Estimate arrival time at a stop based on:
    - Current bus position (distance covered)
    - Average speed or scheduled time
    - Current delay

    Returns dict with eta_minutes and eta_time string.
    """
    stop_map = {s.stop_name: s for s in route_stops}
    if target_stop_name not in stop_map:
        return None

    target_stop = stop_map[target_stop_name]

    # If bus hasn't passed the stop yet
    if bus.distance_covered_km >= target_stop.distance_from_origin_km:
        return {
            "eta_minutes": 0,
            "eta_time": "Arrived / Passed",
            "delay_minutes": bus.delay_minutes,
            "status": bus.status.value,
        }

    remaining_km = (
        target_stop.distance_from_origin_km - bus.distance_covered_km
    )

    # Use scheduled time + delay as primary estimate
    # Find current position's scheduled time
    current_scheduled_mins = target_stop.scheduled_minutes_from_origin

    # Adjust for delay
    eta_minutes = max(0, current_scheduled_mins + bus.delay_minutes)

    # If we have live speed, use distance-based estimate as secondary
    if bus.current_speed_kmh and bus.current_speed_kmh > 5:
        speed_based_mins = int((remaining_km / bus.current_speed_kmh) * 60)
        # Blend schedule-based and speed-based (60/40 weight)
        eta_minutes = int(eta_minutes * 0.6 + speed_based_mins * 0.4)

    from datetime import timedelta
    eta_time = datetime.now(timezone.utc) + timedelta(minutes=eta_minutes)
    # Convert to IST (UTC+5:30)
    from datetime import timezone as tz
    ist_offset = tz(timedelta(hours=5, minutes=30))
    eta_ist = eta_time.astimezone(ist_offset)

    return {
        "eta_minutes": eta_minutes,
        "eta_time": eta_ist.strftime("%I:%M %p"),
        "delay_minutes": bus.delay_minutes,
        "status": bus.status.value,
        "remaining_km": round(remaining_km, 1),
    }


# ── Get Buses for Route ───────────────────────────────────────────────────────
async def get_buses_on_route(
    route_id: str,
    db: AsyncSession,
    redis: aioredis.Redis,
) -> list[dict]:
    """
    Returns all active buses currently running on a route
    with their live locations and ETAs.
    """
    result = await db.execute(
        select(Bus).where(
            and_(
                Bus.route_id == route_id,
                Bus.is_active == True,
                Bus.status.in_([
                    BusStatus.RUNNING,
                    BusStatus.DELAYED,
                    BusStatus.STOPPED,
                ]),
            )
        )
    )
    buses = result.scalars().all()

    # Fetch route stops for ETA calculation
    stops_result = await db.execute(
        select(RouteStop)
        .where(RouteStop.route_id == route_id)
        .order_by(RouteStop.stop_order)
    )
    route_stops = stops_result.scalars().all()

    bus_list = []
    for bus in buses:
        location = await get_bus_location(bus.id, redis, db)
        bus_list.append({
            "bus_id": bus.id,
            "bus_number": bus.bus_number,
            "bus_type": bus.bus_type.value,
            "status": bus.status.value,
            "delay_minutes": bus.delay_minutes,
            "eta_display": bus.eta_display,
            "current_stop": bus.current_stop,
            "next_stop": bus.next_stop,
            "location": location,
            "conductor_name": bus.conductor_name,
            "conductor_mobile": bus.conductor_mobile,
            "seating_capacity": bus.seating_capacity,
            "standing_capacity": bus.standing_capacity,
        })

    return bus_list


# ── Search Buses Between Stops ────────────────────────────────────────────────
async def search_buses(
    boarding_stop: str,
    destination_stop: str,
    db: AsyncSession,
    redis: aioredis.Redis,
) -> list[dict]:
    """
    Find all buses that serve both the boarding and destination stops
    in the correct order (boarding before destination).
    """
    from sqlalchemy.orm import aliased

    # Find routes where both stops exist in correct order
    boarding_alias = aliased(RouteStop)
    destination_alias = aliased(RouteStop)

    result = await db.execute(
        select(Route)
        .join(boarding_alias, boarding_alias.route_id == Route.id)
        .join(destination_alias, destination_alias.route_id == Route.id)
        .where(
            and_(
                boarding_alias.stop_name.ilike(f"%{boarding_stop}%"),
                destination_alias.stop_name.ilike(f"%{destination_stop}%"),
                boarding_alias.stop_order < destination_alias.stop_order,
                Route.is_active == True,
            )
        )
        .distinct()
    )
    routes = result.scalars().all()

    all_buses = []
    for route in routes:
        buses = await get_buses_on_route(route.id, db, redis)

        # Fetch stops for fare calculation
        stops_result = await db.execute(
            select(RouteStop)
            .where(RouteStop.route_id == route.id)
            .order_by(RouteStop.stop_order)
        )
        route_stops = stops_result.scalars().all()

        # Calculate fare for this route segment
        from app.services.fare_engine import fare_engine
        try:
            # Find actual matching stop names (case-insensitive search)
            actual_boarding = next(
                s.stop_name for s in route_stops
                if boarding_stop.lower() in s.stop_name.lower()
            )
            actual_destination = next(
                s.stop_name for s in route_stops
                if destination_stop.lower() in s.stop_name.lower()
            )
            fare = fare_engine.calculate_from_stops(
                route_stops=route_stops,
                boarding_stop_name=actual_boarding,
                destination_stop_name=actual_destination,
            )
            fare_info = {
                "adult_fare_rupees": fare.adult_fare_rupees,
                "distance_km": fare.distance_km,
            }
        except (ValueError, StopIteration):
            fare_info = {"adult_fare_rupees": None, "distance_km": None}

        for bus in buses:
            # Calculate ETA to boarding stop
            bus_obj = next((b for b in [bus] if b["bus_id"] == bus["bus_id"]), None)
            all_buses.append({
                **bus,
                "route_number": route.route_number,
                "route_name": route.name,
                "boarding_stop": actual_boarding if "actual_boarding" in dir() else boarding_stop,
                "destination_stop": actual_destination if "actual_destination" in dir() else destination_stop,
                "fare_info": fare_info,
            })

    return all_buses