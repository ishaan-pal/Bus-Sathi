from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as aioredis

from app.core.dependencies import (
    get_db,
    get_redis,
    get_optional_user,
    get_current_admin,
    verify_bus_tracking_api_key,
)
from app.models.bus import Bus, BusStatus
from app.models.route import Route, RouteStop
from app.services.bus_tracking import (
    search_buses,
    get_bus_location,
    get_buses_on_route,
    update_bus_location,
    calculate_eta,
)
from app.schemas.bus import (
    BusSearchRequest,
    BusSearchResponse,
    BusSearchResultItem,
    BusDetailResponse,
    BusLocationResponse,
    UpdateLocationRequest,
    ETAResponse,
    RouteResponse,
    RouteStopResponse,
    StopsListResponse,
    CreateBusRequest,
    UpdateBusStatusRequest,
    AdminBusListItem,
    FareInfoResponse,
)

router = APIRouter(prefix="/buses", tags=["Buses & Tracking"])


# ── Search Buses ──────────────────────────────────────────────────────────────
@router.post(
    "/search",
    response_model=BusSearchResponse,
    summary="Search buses between two stops",
)
async def search_buses_endpoint(
    body: BusSearchRequest,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    current_user=Depends(get_optional_user),
):
    """
    Search for available buses between boarding and destination stops.
    Available to both guests and registered users.
    Returns live bus locations, ETA, and fare info.
    """
    results = await search_buses(
        boarding_stop=body.boarding_stop,
        destination_stop=body.destination_stop,
        db=db,
        redis=redis,
    )

    bus_items = []
    for b in results:
        loc = b.get("location")
        bus_items.append(
            BusSearchResultItem(
                bus_id=b["bus_id"],
                bus_number=b["bus_number"],
                bus_type=b["bus_type"],
                status=b["status"],
                delay_minutes=b["delay_minutes"],
                eta_display=b["eta_display"],
                current_stop=b.get("current_stop"),
                next_stop=b.get("next_stop"),
                route_number=b["route_number"],
                route_name=b["route_name"],
                boarding_stop=b["boarding_stop"],
                destination_stop=b["destination_stop"],
                fare_info=FareInfoResponse(
                    adult_fare_rupees=b["fare_info"].get("adult_fare_rupees"),
                    distance_km=b["fare_info"].get("distance_km"),
                ),
                location=BusLocationResponse(**loc) if loc else None,
                conductor_name=b.get("conductor_name"),
                conductor_mobile=b.get("conductor_mobile"),
                seating_capacity=b["seating_capacity"],
                standing_capacity=b["standing_capacity"],
            )
        )

    return BusSearchResponse(
        success=True,
        boarding_stop=body.boarding_stop,
        destination_stop=body.destination_stop,
        total_results=len(bus_items),
        buses=bus_items,
    )


# ── Get Bus Detail ────────────────────────────────────────────────────────────
@router.get(
    "/{bus_id}",
    response_model=BusDetailResponse,
    summary="Get full bus detail with live location",
)
async def get_bus_detail(
    bus_id: str,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    current_user=Depends(get_optional_user),
):
    """
    Get detailed info for a specific bus including live location.
    Available to guests and registered users.
    """
    result = await db.execute(
        select(Bus).where(Bus.id == bus_id)
    )
    bus = result.scalar_one_or_none()
    if not bus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bus not found",
        )

    location = await get_bus_location(bus_id, redis, db)

    # Fetch route info
    route_number = None
    route_name = None
    if bus.route_id:
        route_result = await db.execute(
            select(Route).where(Route.id == bus.route_id)
        )
        route = route_result.scalar_one_or_none()
        if route:
            route_number = route.route_number
            route_name = route.name

    return BusDetailResponse(
        bus_id=bus.id,
        bus_number=bus.bus_number,
        registration_number=bus.registration_number,
        bus_type=bus.bus_type.value,
        status=bus.status.value,
        delay_minutes=bus.delay_minutes,
        eta_display=bus.eta_display,
        current_stop=bus.current_stop,
        next_stop=bus.next_stop,
        distance_covered_km=bus.distance_covered_km,
        driver_name=bus.driver_name,
        conductor_name=bus.conductor_name,
        conductor_mobile=bus.conductor_mobile,
        seating_capacity=bus.seating_capacity,
        standing_capacity=bus.standing_capacity,
        tracking_source=bus.tracking_source,
        route_number=route_number,
        route_name=route_name,
        location=BusLocationResponse(**location) if location else None,
        is_location_stale=bus.is_location_stale,
    )


# ── Live Location ─────────────────────────────────────────────────────────────
@router.get(
    "/{bus_id}/location",
    response_model=BusLocationResponse,
    summary="Get live location of a bus",
)
async def get_live_location(
    bus_id: str,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    current_user=Depends(get_optional_user),
):
    """
    Returns the latest GPS location of a bus.
    Guests and registered users can both access this.
    Marks location as stale if not updated within threshold.
    """
    location = await get_bus_location(bus_id, redis, db)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location data not available for this bus",
        )
    return BusLocationResponse(**location)


# ── ETA ───────────────────────────────────────────────────────────────────────
@router.get(
    "/{bus_id}/eta",
    response_model=ETAResponse,
    summary="Get ETA for a bus to reach a stop",
)
async def get_eta(
    bus_id: str,
    stop: str = Query(..., description="Stop name to calculate ETA for"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """
    Calculate ETA for a bus to reach the specified stop.
    Uses schedule + live speed data for estimation.
    Available to guests and registered users.
    """
    result = await db.execute(select(Bus).where(Bus.id == bus_id))
    bus = result.scalar_one_or_none()
    if not bus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bus not found",
        )
    if not bus.route_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bus has no assigned route",
        )

    stops_result = await db.execute(
        select(RouteStop)
        .where(RouteStop.route_id == bus.route_id)
        .order_by(RouteStop.stop_order)
    )
    route_stops = stops_result.scalars().all()

    eta = await calculate_eta(
        bus=bus,
        target_stop_name=stop,
        route_stops=route_stops,
    )
    if not eta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stop '{stop}' not found on this bus route",
        )
    return ETAResponse(**eta)


# ── All Stops (for search dropdowns) ─────────────────────────────────────────
@router.get(
    "/stops/all",
    response_model=StopsListResponse,
    summary="Get all unique bus stop names",
)
async def get_all_stops(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """Returns sorted unique stop names from all active routes."""
    result = await db.execute(
        select(RouteStop.stop_name)
        .join(Route, RouteStop.route_id == Route.id)
        .where(Route.is_active == True)
        .distinct()
        .order_by(RouteStop.stop_name)
    )
    stops = [row[0] for row in result.fetchall()]
    return StopsListResponse(stops=stops, total=len(stops))


# ── All Routes ────────────────────────────────────────────────────────────────
@router.get(
    "/routes/all",
    response_model=list[RouteResponse],
    summary="Get all active routes with stops",
)
async def get_all_routes(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """
    Returns all active routes with their stop details.
    Used to populate journey search dropdowns.
    """
    result = await db.execute(
        select(Route).where(Route.is_active == True)
        .order_by(Route.route_number)
    )
    routes = result.scalars().all()

    route_list = []
    for route in routes:
        stops_result = await db.execute(
            select(RouteStop)
            .where(RouteStop.route_id == route.id)
            .order_by(RouteStop.stop_order)
        )
        stops = stops_result.scalars().all()
        route_list.append(
            RouteResponse(
                id=route.id,
                route_number=route.route_number,
                name=route.name,
                origin=route.origin,
                destination=route.destination,
                total_distance_km=route.total_distance_km,
                estimated_duration_minutes=route.estimated_duration_minutes,
                is_active=route.is_active,
                stops=[
                    RouteStopResponse(
                        stop_name=s.stop_name,
                        stop_order=s.stop_order,
                        distance_from_origin_km=s.distance_from_origin_km,
                        latitude=s.latitude,
                        longitude=s.longitude,
                        scheduled_minutes_from_origin=s.scheduled_minutes_from_origin,
                        is_major_stop=s.is_major_stop,
                    )
                    for s in stops
                ],
            )
        )
    return route_list


# ── GPS Update (called by bus GPS device / ETM) ───────────────────────────────
@router.post(
    "/location/update",
    summary="Update bus GPS location (GPS device / ETM feed)",
)
async def update_location(
    body: UpdateLocationRequest,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    _: None = Depends(verify_bus_tracking_api_key),
):
    """
    Called by the bus GPS device or ETM machine feed to push
    live location updates. Requires X-API-Key header when
    BUS_TRACKING_API_KEY is set (required in production).
    """
    success = await update_bus_location(
        bus_id=body.bus_id,
        latitude=body.latitude,
        longitude=body.longitude,
        speed_kmh=body.speed_kmh,
        heading=body.heading,
        redis=redis,
        db=db,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bus not found",
        )
    return {
        "success": True,
        "message": "Location updated",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Admin: List All Buses ─────────────────────────────────────────────────────
@router.get(
    "/admin/all",
    response_model=list[AdminBusListItem],
    summary="[Admin] List all buses",
)
async def admin_list_buses(
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Admin endpoint to list all buses with status."""
    result = await db.execute(
        select(Bus).order_by(Bus.bus_number)
    )
    buses = result.scalars().all()

    items = []
    for bus in buses:
        route_number = None
        if bus.route_id:
            r = await db.execute(
                select(Route.route_number).where(Route.id == bus.route_id)
            )
            route_number = r.scalar_one_or_none()

        items.append(
            AdminBusListItem(
                id=bus.id,
                bus_number=bus.bus_number,
                registration_number=bus.registration_number,
                bus_type=bus.bus_type.value,
                status=bus.status.value,
                is_active=bus.is_active,
                route_number=route_number,
                current_stop=bus.current_stop,
                delay_minutes=bus.delay_minutes,
                last_location_update=(
                    bus.last_location_update.isoformat()
                    if bus.last_location_update else None
                ),
                driver_name=bus.driver_name,
                conductor_name=bus.conductor_name,
            )
        )
    return items


# ── Admin: Create Bus ─────────────────────────────────────────────────────────
@router.post(
    "/admin/create",
    summary="[Admin] Add a new bus",
)
async def admin_create_bus(
    body: CreateBusRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Admin endpoint to register a new bus."""
    import uuid
    bus = Bus(
        id=str(uuid.uuid4()),
        bus_number=body.bus_number,
        registration_number=body.registration_number,
        bus_type=body.bus_type,
        route_id=body.route_id,
        seating_capacity=body.seating_capacity,
        standing_capacity=body.standing_capacity,
        driver_name=body.driver_name,
        conductor_name=body.conductor_name,
        conductor_mobile=body.conductor_mobile,
        status=BusStatus.DEPOT,
        is_active=True,
    )
    db.add(bus)
    await db.commit()
    await db.refresh(bus)
    return {"success": True, "bus_id": bus.id, "bus_number": bus.bus_number}


# ── Admin: Update Bus Status ──────────────────────────────────────────────────
@router.patch(
    "/admin/{bus_id}/status",
    summary="[Admin] Update bus operational status",
)
async def admin_update_bus_status(
    bus_id: str,
    body: UpdateBusStatusRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Admin endpoint to update bus status and delay info."""
    result = await db.execute(select(Bus).where(Bus.id == bus_id))
    bus = result.scalar_one_or_none()
    if not bus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bus not found",
        )
    bus.status = body.status
    bus.delay_minutes = body.delay_minutes or 0
    if body.current_stop:
        bus.current_stop = body.current_stop
    if body.next_stop:
        bus.next_stop = body.next_stop
    await db.commit()
    return {"success": True, "message": "Bus status updated"}