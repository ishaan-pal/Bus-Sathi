import csv
import hashlib
import io
import secrets
import uuid
from datetime import date, time
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bus import Bus, BusType
from app.models.depot import Depot
from app.models.driver import Driver, StaffRole
from app.models.route import Route
from app.models.tracking_api_key import TrackingApiKey
from app.models.trip_assignment import TripAssignment


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def generate_api_key() -> str:
    return f"hr_{secrets.token_urlsafe(32)}"


async def verify_tracking_api_key(
    raw_key: str,
    db: AsyncSession,
    legacy_key: Optional[str] = None,
) -> Optional[str]:
    """
    Validate a tracking API key against the legacy env key or DB keys.
    Returns the tracking_api_keys.id when matched in DB, or 'legacy' for env key.
    """
    if legacy_key and secrets.compare_digest(raw_key, legacy_key):
        return "legacy"

    key_hash = hash_api_key(raw_key)
    result = await db.execute(
        select(TrackingApiKey).where(
            TrackingApiKey.key_hash == key_hash,
            TrackingApiKey.is_active == True,
        )
    )
    record = result.scalar_one_or_none()
    if record:
        from datetime import datetime, timezone

        record.last_used_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await db.commit()
        return record.id
    return None


async def resolve_bus_for_location_update(
    db: AsyncSession,
    bus_id: Optional[str],
    gps_device_id: Optional[str],
) -> Optional[Bus]:
    if bus_id:
        result = await db.execute(select(Bus).where(Bus.id == bus_id))
        return result.scalar_one_or_none()
    if gps_device_id:
        result = await db.execute(
            select(Bus).where(Bus.gps_device_id == gps_device_id.strip())
        )
        return result.scalar_one_or_none()
    return None


async def sync_bus_crew_names(
    db: AsyncSession,
    bus: Bus,
    driver_id: Optional[str] = None,
    conductor_id: Optional[str] = None,
) -> None:
    """Copy driver/conductor names from staff records onto the bus."""
    if driver_id is not None:
        bus.driver_id = driver_id or None
        if driver_id:
            result = await db.execute(select(Driver).where(Driver.id == driver_id))
            driver = result.scalar_one_or_none()
            bus.driver_name = driver.name if driver else None
        else:
            bus.driver_name = None

    if conductor_id is not None:
        bus.conductor_id = conductor_id or None
        if conductor_id:
            result = await db.execute(
                select(Driver).where(Driver.id == conductor_id)
            )
            conductor = result.scalar_one_or_none()
            if conductor:
                bus.conductor_name = conductor.name
                bus.conductor_mobile = conductor.mobile
            else:
                bus.conductor_name = None
                bus.conductor_mobile = None
        else:
            bus.conductor_name = None
            bus.conductor_mobile = None


async def apply_trip_assignment_to_bus(
    db: AsyncSession,
    assignment: TripAssignment,
) -> None:
    result = await db.execute(select(Bus).where(Bus.id == assignment.bus_id))
    bus = result.scalar_one_or_none()
    if not bus:
        return

    bus.route_id = assignment.route_id
    await sync_bus_crew_names(
        db,
        bus,
        driver_id=assignment.driver_id,
        conductor_id=assignment.conductor_id,
    )


def parse_time(value: str) -> Optional[time]:
    value = value.strip()
    if not value:
        return None
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            from datetime import datetime

            return datetime.strptime(value, fmt).time()
        except ValueError:
            continue
    raise ValueError(f"Invalid time format: {value}")


async def import_drivers_csv(db: AsyncSession, csv_text: str) -> dict:
    """
    CSV columns:
    employee_id,name,mobile,license_number,depot_code,role
    """
    reader = csv.DictReader(io.StringIO(csv_text.strip()))
    created = 0
    updated = 0
    errors: list[str] = []

    depot_result = await db.execute(select(Depot))
    depot_map = {d.code.upper(): d.id for d in depot_result.scalars().all()}

    for row_num, row in enumerate(reader, start=2):
        try:
            employee_id = row.get("employee_id", "").strip()
            name = row.get("name", "").strip()
            if not employee_id or not name:
                errors.append(f"Row {row_num}: employee_id and name are required")
                continue

            mobile = row.get("mobile", "").strip() or None
            license_number = row.get("license_number", "").strip() or None
            depot_code = row.get("depot_code", "").strip().upper()
            depot_id = depot_map.get(depot_code) if depot_code else None
            if depot_code and not depot_id:
                errors.append(f"Row {row_num}: unknown depot_code '{depot_code}'")
                continue

            role_str = row.get("role", "driver").strip().lower()
            try:
                role = StaffRole(role_str)
            except ValueError:
                errors.append(f"Row {row_num}: invalid role '{role_str}'")
                continue

            existing = await db.execute(
                select(Driver).where(Driver.employee_id == employee_id)
            )
            driver = existing.scalar_one_or_none()
            if driver:
                driver.name = name
                driver.mobile = mobile
                driver.license_number = license_number
                driver.depot_id = depot_id
                driver.role = role
                driver.is_active = True
                updated += 1
            else:
                db.add(
                    Driver(
                        id=str(uuid.uuid4()),
                        employee_id=employee_id,
                        name=name,
                        mobile=mobile,
                        license_number=license_number,
                        depot_id=depot_id,
                        role=role,
                        is_active=True,
                    )
                )
                created += 1
        except Exception as exc:
            errors.append(f"Row {row_num}: {exc}")

    await db.commit()
    return {"created": created, "updated": updated, "errors": errors}


async def import_buses_csv(db: AsyncSession, csv_text: str) -> dict:
    """
    CSV columns:
    bus_number,registration_number,bus_type,route_number,seating_capacity,
    standing_capacity,gps_device_id,driver_employee_id,conductor_employee_id
    """
    reader = csv.DictReader(io.StringIO(csv_text.strip()))
    created = 0
    updated = 0
    errors: list[str] = []

    route_result = await db.execute(select(Route))
    route_map = {r.route_number.upper(): r.id for r in route_result.scalars().all()}

    driver_result = await db.execute(select(Driver))
    driver_map = {d.employee_id: d for d in driver_result.scalars().all()}

    for row_num, row in enumerate(reader, start=2):
        try:
            bus_number = row.get("bus_number", "").strip().upper()
            registration_number = row.get("registration_number", "").strip().upper()
            if not bus_number or not registration_number:
                errors.append(
                    f"Row {row_num}: bus_number and registration_number are required"
                )
                continue

            bus_type_str = row.get("bus_type", "ordinary").strip().lower()
            try:
                bus_type = BusType(bus_type_str)
            except ValueError:
                errors.append(f"Row {row_num}: invalid bus_type '{bus_type_str}'")
                continue

            route_number = row.get("route_number", "").strip().upper()
            route_id = route_map.get(route_number) if route_number else None
            if route_number and not route_id:
                errors.append(f"Row {row_num}: unknown route_number '{route_number}'")
                continue

            seating = int(row.get("seating_capacity") or 52)
            standing = int(row.get("standing_capacity") or 20)
            gps_device_id = row.get("gps_device_id", "").strip() or None

            driver_emp = row.get("driver_employee_id", "").strip()
            conductor_emp = row.get("conductor_employee_id", "").strip()
            driver = driver_map.get(driver_emp) if driver_emp else None
            conductor = driver_map.get(conductor_emp) if conductor_emp else None
            if driver_emp and not driver:
                errors.append(
                    f"Row {row_num}: unknown driver_employee_id '{driver_emp}'"
                )
                continue
            if conductor_emp and not conductor:
                errors.append(
                    f"Row {row_num}: unknown conductor_employee_id '{conductor_emp}'"
                )
                continue

            existing = await db.execute(
                select(Bus).where(Bus.bus_number == bus_number)
            )
            bus = existing.scalar_one_or_none()
            if bus:
                bus.registration_number = registration_number
                bus.bus_type = bus_type
                bus.route_id = route_id
                bus.seating_capacity = seating
                bus.standing_capacity = standing
                bus.gps_device_id = gps_device_id
                if driver:
                    bus.driver_id = driver.id
                    bus.driver_name = driver.name
                if conductor:
                    bus.conductor_id = conductor.id
                    bus.conductor_name = conductor.name
                    bus.conductor_mobile = conductor.mobile
                updated += 1
            else:
                db.add(
                    Bus(
                        id=str(uuid.uuid4()),
                        bus_number=bus_number,
                        registration_number=registration_number,
                        bus_type=bus_type,
                        route_id=route_id,
                        seating_capacity=seating,
                        standing_capacity=standing,
                        gps_device_id=gps_device_id,
                        driver_id=driver.id if driver else None,
                        conductor_id=conductor.id if conductor else None,
                        driver_name=driver.name if driver else None,
                        conductor_name=conductor.name if conductor else None,
                        conductor_mobile=conductor.mobile if conductor else None,
                        is_active=True,
                    )
                )
                created += 1
        except Exception as exc:
            errors.append(f"Row {row_num}: {exc}")

    await db.commit()
    return {"created": created, "updated": updated, "errors": errors}


async def get_driver_by_id(db: AsyncSession, driver_id: str) -> Driver:
    result = await db.execute(select(Driver).where(Driver.id == driver_id))
    driver = result.scalar_one_or_none()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found",
        )
    return driver


async def get_depot_by_id(db: AsyncSession, depot_id: str) -> Depot:
    result = await db.execute(select(Depot).where(Depot.id == depot_id))
    depot = result.scalar_one_or_none()
    if not depot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Depot not found",
        )
    return depot
