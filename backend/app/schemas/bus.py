from pydantic import BaseModel, field_validator
from typing import Optional
from app.models.bus import BusStatus, BusType


# ── Location Schemas ──────────────────────────────────────────────────────────
class BusLocationResponse(BaseModel):
    bus_id: str
    bus_number: str
    latitude: float
    longitude: float
    speed_kmh: Optional[float]
    heading: Optional[float]
    status: str
    delay_minutes: int
    current_stop: Optional[str]
    next_stop: Optional[str]
    last_updated: Optional[str]
    is_stale: bool


class UpdateLocationRequest(BaseModel):
    bus_id: str
    latitude: float
    longitude: float
    speed_kmh: Optional[float] = None
    heading: Optional[float] = None

    @field_validator("latitude")
    @classmethod
    def check_latitude(cls, v):
        if not (-90 <= v <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        # Haryana bounding box check (loose)
        if not (27.5 <= v <= 31.5):
            raise ValueError("Location appears to be outside Haryana")
        return v

    @field_validator("longitude")
    @classmethod
    def check_longitude(cls, v):
        if not (-180 <= v <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        # Haryana bounding box check (loose)
        if not (74.5 <= v <= 77.5):
            raise ValueError("Location appears to be outside Haryana")
        return v


# ── ETA Schema ────────────────────────────────────────────────────────────────
class ETAResponse(BaseModel):
    eta_minutes: int
    eta_time: str
    delay_minutes: int
    status: str
    remaining_km: Optional[float] = None


# ── Bus Search Schemas ────────────────────────────────────────────────────────
class BusSearchRequest(BaseModel):
    boarding_stop: str
    destination_stop: str

    @field_validator("boarding_stop", "destination_stop")
    @classmethod
    def check_stop(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Stop name must be at least 2 characters")
        if len(v) > 100:
            raise ValueError("Stop name must be under 100 characters")
        return v


class FareInfoResponse(BaseModel):
    adult_fare_rupees: Optional[float]
    distance_km: Optional[float]


class BusSearchResultItem(BaseModel):
    bus_id: str
    bus_number: str
    bus_type: str
    status: str
    delay_minutes: int
    eta_display: str
    current_stop: Optional[str]
    next_stop: Optional[str]
    route_number: str
    route_name: str
    boarding_stop: str
    destination_stop: str
    fare_info: FareInfoResponse
    location: Optional[BusLocationResponse]
    conductor_name: Optional[str]
    conductor_mobile: Optional[str]
    seating_capacity: int
    standing_capacity: int


class BusSearchResponse(BaseModel):
    success: bool
    boarding_stop: str
    destination_stop: str
    total_results: int
    buses: list[BusSearchResultItem]


# ── Bus Detail Schema ─────────────────────────────────────────────────────────
class BusDetailResponse(BaseModel):
    bus_id: str
    bus_number: str
    registration_number: str
    bus_type: str
    status: str
    delay_minutes: int
    eta_display: str
    current_stop: Optional[str]
    next_stop: Optional[str]
    distance_covered_km: float
    driver_name: Optional[str]
    conductor_name: Optional[str]
    conductor_mobile: Optional[str]
    seating_capacity: int
    standing_capacity: int
    tracking_source: str
    route_number: Optional[str]
    route_name: Optional[str]
    location: Optional[BusLocationResponse]
    is_location_stale: bool

    model_config = {"from_attributes": True}


# ── Stop Schema ───────────────────────────────────────────────────────────────
class RouteStopResponse(BaseModel):
    stop_name: str
    stop_order: int
    distance_from_origin_km: float
    latitude: Optional[float]
    longitude: Optional[float]
    scheduled_minutes_from_origin: int
    is_major_stop: bool

    model_config = {"from_attributes": True}


# ── Route Schema ──────────────────────────────────────────────────────────────
class RouteResponse(BaseModel):
    id: str
    route_number: str
    name: str
    origin: str
    destination: str
    total_distance_km: float
    estimated_duration_minutes: int
    is_active: bool
    stops: list[RouteStopResponse] = []

    model_config = {"from_attributes": True}


# ── Admin Schemas ─────────────────────────────────────────────────────────────
class CreateBusRequest(BaseModel):
    bus_number: str
    registration_number: str
    bus_type: BusType = BusType.ORDINARY
    route_id: Optional[str] = None
    seating_capacity: int = 52
    standing_capacity: int = 20
    driver_name: Optional[str] = None
    conductor_name: Optional[str] = None
    conductor_mobile: Optional[str] = None

    @field_validator("bus_number")
    @classmethod
    def check_bus_number(cls, v):
        v = v.strip().upper()
        if len(v) < 4:
            raise ValueError("Bus number too short")
        return v

    @field_validator("conductor_mobile")
    @classmethod
    def check_conductor_mobile(cls, v):
        import re
        if v is not None:
            v = v.strip()
            if not re.fullmatch(r"[6-9]\d{9}", v):
                raise ValueError("Invalid conductor mobile number")
        return v


class UpdateBusStatusRequest(BaseModel):
    status: BusStatus
    delay_minutes: Optional[int] = 0
    current_stop: Optional[str] = None
    next_stop: Optional[str] = None


class AdminBusListItem(BaseModel):
    id: str
    bus_number: str
    registration_number: str
    bus_type: str
    status: str
    is_active: bool
    route_number: Optional[str]
    current_stop: Optional[str]
    delay_minutes: int
    last_location_update: Optional[str]
    driver_name: Optional[str]
    conductor_name: Optional[str]

    model_config = {"from_attributes": True}