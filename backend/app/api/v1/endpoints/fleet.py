import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.dependencies import get_db, get_current_admin
from app.models.bus import Bus
from app.models.depot import Depot
from app.models.driver import Driver
from app.models.route import Route
from app.models.tracking_api_key import TrackingApiKey
from app.models.trip_assignment import TripAssignment
from app.schemas.fleet import (
    DepotResponse,
    CreateDriverRequest,
    UpdateDriverRequest,
    DriverResponse,
    CreateTripAssignmentRequest,
    TripAssignmentResponse,
    CreateTrackingKeyRequest,
    TrackingKeyResponse,
    TrackingKeyCreatedResponse,
    CsvImportRequest,
    CsvImportResponse,
)
from app.services.fleet import (
    apply_trip_assignment_to_bus,
    generate_api_key,
    get_depot_by_id,
    get_driver_by_id,
    hash_api_key,
    import_buses_csv,
    import_drivers_csv,
    sync_bus_crew_names,
)

router = APIRouter(prefix="/admin/fleet", tags=["Admin Fleet"])


def _driver_response(driver: Driver, depot: Depot | None = None) -> DriverResponse:
    return DriverResponse(
        id=driver.id,
        employee_id=driver.employee_id,
        name=driver.name,
        mobile=driver.mobile,
        license_number=driver.license_number,
        depot_id=driver.depot_id,
        depot_code=depot.code if depot else None,
        depot_name=depot.name if depot else None,
        role=driver.role.value,
        is_active=driver.is_active,
    )


def _trip_response(
    assignment: TripAssignment,
    bus: Bus | None = None,
    driver: Driver | None = None,
    conductor: Driver | None = None,
    route: Route | None = None,
) -> TripAssignmentResponse:
    return TripAssignmentResponse(
        id=assignment.id,
        assignment_date=assignment.assignment_date.isoformat(),
        bus_id=assignment.bus_id,
        bus_number=bus.bus_number if bus else None,
        driver_id=assignment.driver_id,
        driver_name=driver.name if driver else None,
        conductor_id=assignment.conductor_id,
        conductor_name=conductor.name if conductor else None,
        route_id=assignment.route_id,
        route_number=route.route_number if route else None,
        scheduled_departure=(
            assignment.scheduled_departure.isoformat()
            if assignment.scheduled_departure
            else None
        ),
        is_active=assignment.is_active,
        notes=assignment.notes,
    )


# ── Depots ────────────────────────────────────────────────────────────────────
@router.get("/depots", response_model=list[DepotResponse])
async def list_depots(
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    result = await db.execute(select(Depot).order_by(Depot.code))
    return result.scalars().all()


# ── Drivers ───────────────────────────────────────────────────────────────────
@router.get("/drivers", response_model=list[DriverResponse])
async def list_drivers(
    active_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    query = select(Driver, Depot).outerjoin(Depot, Driver.depot_id == Depot.id)
    if active_only:
        query = query.where(Driver.is_active == True)
    query = query.order_by(Driver.employee_id)
    result = await db.execute(query)
    rows = result.all()
    return [_driver_response(driver, depot) for driver, depot in rows]


@router.post("/drivers", response_model=DriverResponse)
async def create_driver(
    body: CreateDriverRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    existing = await db.execute(
        select(Driver).where(Driver.employee_id == body.employee_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee ID already exists",
        )

    depot = None
    if body.depot_id:
        depot = await get_depot_by_id(db, body.depot_id)

    driver = Driver(
        id=str(uuid.uuid4()),
        employee_id=body.employee_id,
        name=body.name,
        mobile=body.mobile,
        license_number=body.license_number,
        depot_id=body.depot_id,
        role=body.role,
        is_active=True,
    )
    db.add(driver)
    await db.commit()
    await db.refresh(driver)
    return _driver_response(driver, depot)


@router.patch("/drivers/{driver_id}", response_model=DriverResponse)
async def update_driver(
    driver_id: str,
    body: UpdateDriverRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    driver = await get_driver_by_id(db, driver_id)
    if body.name is not None:
        driver.name = body.name
    if body.mobile is not None:
        driver.mobile = body.mobile or None
    if body.license_number is not None:
        driver.license_number = body.license_number or None
    if body.depot_id is not None:
        if body.depot_id:
            await get_depot_by_id(db, body.depot_id)
        driver.depot_id = body.depot_id or None
    if body.role is not None:
        driver.role = body.role
    if body.is_active is not None:
        driver.is_active = body.is_active

    await db.commit()
    await db.refresh(driver)

    depot = None
    if driver.depot_id:
        depot = await get_depot_by_id(db, driver.depot_id)
    return _driver_response(driver, depot)


@router.post("/drivers/import", response_model=CsvImportResponse)
async def import_drivers(
    body: CsvImportRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    result = await import_drivers_csv(db, body.csv_text)
    return CsvImportResponse(
        success=len(result["errors"]) == 0,
        created=result["created"],
        updated=result["updated"],
        errors=result["errors"],
    )


# ── Trip Assignments ──────────────────────────────────────────────────────────
@router.get("/assignments", response_model=list[TripAssignmentResponse])
async def list_trip_assignments(
    assignment_date: date | None = Query(None),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    query = (
        select(TripAssignment, Bus, Driver, Route)
        .join(Bus, TripAssignment.bus_id == Bus.id)
        .join(Driver, TripAssignment.driver_id == Driver.id)
        .join(Route, TripAssignment.route_id == Route.id)
    )
    if assignment_date:
        query = query.where(TripAssignment.assignment_date == assignment_date)
    if active_only:
        query = query.where(TripAssignment.is_active == True)
    query = query.order_by(
        TripAssignment.assignment_date.desc(),
        TripAssignment.scheduled_departure,
    )
    result = await db.execute(query)
    items = []
    for assignment, bus, driver, route in result.all():
        conductor = None
        if assignment.conductor_id:
            c_result = await db.execute(
                select(Driver).where(Driver.id == assignment.conductor_id)
            )
            conductor = c_result.scalar_one_or_none()
        items.append(_trip_response(assignment, bus, driver, conductor, route))
    return items


@router.post("/assignments", response_model=TripAssignmentResponse)
async def create_trip_assignment(
    body: CreateTripAssignmentRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    bus_result = await db.execute(select(Bus).where(Bus.id == body.bus_id))
    bus = bus_result.scalar_one_or_none()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")

    driver = await get_driver_by_id(db, body.driver_id)
    conductor = None
    if body.conductor_id:
        conductor = await get_driver_by_id(db, body.conductor_id)

    route_result = await db.execute(select(Route).where(Route.id == body.route_id))
    route = route_result.scalar_one_or_none()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    assignment = TripAssignment(
        id=str(uuid.uuid4()),
        assignment_date=body.assignment_date,
        bus_id=body.bus_id,
        driver_id=body.driver_id,
        conductor_id=body.conductor_id,
        route_id=body.route_id,
        scheduled_departure=body.scheduled_departure,
        notes=body.notes,
        is_active=True,
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)

    if body.apply_to_bus:
        await apply_trip_assignment_to_bus(db, assignment)
        await db.commit()

    return _trip_response(assignment, bus, driver, conductor, route)


@router.patch("/assignments/{assignment_id}/deactivate")
async def deactivate_trip_assignment(
    assignment_id: str,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    result = await db.execute(
        select(TripAssignment).where(TripAssignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    assignment.is_active = False
    await db.commit()
    return {"success": True, "message": "Assignment deactivated"}


# ── Tracking API Keys ─────────────────────────────────────────────────────────
@router.get("/tracking-keys", response_model=list[TrackingKeyResponse])
async def list_tracking_keys(
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    result = await db.execute(
        select(TrackingApiKey, Depot)
        .outerjoin(Depot, TrackingApiKey.depot_id == Depot.id)
        .order_by(TrackingApiKey.created_at.desc())
    )
    items = []
    for key, depot in result.all():
        items.append(
            TrackingKeyResponse(
                id=key.id,
                label=key.label,
                key_prefix=key.key_prefix,
                depot_id=key.depot_id,
                depot_code=depot.code if depot else None,
                is_active=key.is_active,
                last_used_at=(
                    key.last_used_at.isoformat() if key.last_used_at else None
                ),
                created_at=key.created_at.isoformat(),
            )
        )
    return items


@router.post("/tracking-keys", response_model=TrackingKeyCreatedResponse)
async def create_tracking_key(
    body: CreateTrackingKeyRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    depot = None
    if body.depot_id:
        depot = await get_depot_by_id(db, body.depot_id)

    raw_key = generate_api_key()
    record = TrackingApiKey(
        id=str(uuid.uuid4()),
        label=body.label,
        key_prefix=raw_key[:12],
        key_hash=hash_api_key(raw_key),
        depot_id=body.depot_id,
        is_active=True,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return TrackingKeyCreatedResponse(
        id=record.id,
        label=record.label,
        key_prefix=record.key_prefix,
        depot_id=record.depot_id,
        depot_code=depot.code if depot else None,
        is_active=record.is_active,
        last_used_at=None,
        created_at=record.created_at.isoformat(),
        api_key=raw_key,
    )


@router.patch("/tracking-keys/{key_id}/deactivate")
async def deactivate_tracking_key(
    key_id: str,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    result = await db.execute(
        select(TrackingApiKey).where(TrackingApiKey.id == key_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Tracking key not found")
    record.is_active = False
    await db.commit()
    return {"success": True, "message": "Tracking key deactivated"}


# ── Bulk bus import ───────────────────────────────────────────────────────────
@router.post("/buses/import", response_model=CsvImportResponse)
async def import_buses(
    body: CsvImportRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    result = await import_buses_csv(db, body.csv_text)
    return CsvImportResponse(
        success=len(result["errors"]) == 0,
        created=result["created"],
        updated=result["updated"],
        errors=result["errors"],
    )
