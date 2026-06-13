import re
from datetime import date, time
from typing import Optional

from pydantic import BaseModel, field_validator, model_validator

from app.models.bus import BusType
from app.models.driver import StaffRole


class DepotResponse(BaseModel):
    id: str
    code: str
    name: str
    city: Optional[str]
    is_active: bool

    model_config = {"from_attributes": True}


class CreateDriverRequest(BaseModel):
    employee_id: str
    name: str
    mobile: Optional[str] = None
    license_number: Optional[str] = None
    depot_id: Optional[str] = None
    role: StaffRole = StaffRole.DRIVER

    @field_validator("employee_id")
    @classmethod
    def check_employee_id(cls, v):
        v = v.strip().upper()
        if len(v) < 3:
            raise ValueError("Employee ID too short")
        return v

    @field_validator("name")
    @classmethod
    def check_name(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name too short")
        return v

    @field_validator("mobile")
    @classmethod
    def check_mobile(cls, v):
        if v is not None:
            v = v.strip()
            if v and not re.fullmatch(r"[6-9]\d{9}", v):
                raise ValueError("Invalid mobile number")
        return v


class UpdateDriverRequest(BaseModel):
    name: Optional[str] = None
    mobile: Optional[str] = None
    license_number: Optional[str] = None
    depot_id: Optional[str] = None
    role: Optional[StaffRole] = None
    is_active: Optional[bool] = None

    @field_validator("mobile")
    @classmethod
    def check_mobile(cls, v):
        if v is not None:
            v = v.strip()
            if v and not re.fullmatch(r"[6-9]\d{9}", v):
                raise ValueError("Invalid mobile number")
        return v


class DriverResponse(BaseModel):
    id: str
    employee_id: str
    name: str
    mobile: Optional[str]
    license_number: Optional[str]
    depot_id: Optional[str]
    depot_code: Optional[str] = None
    depot_name: Optional[str] = None
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


class CreateTripAssignmentRequest(BaseModel):
    assignment_date: date
    bus_id: str
    driver_id: str
    conductor_id: Optional[str] = None
    route_id: str
    scheduled_departure: Optional[time] = None
    notes: Optional[str] = None
    apply_to_bus: bool = True


class TripAssignmentResponse(BaseModel):
    id: str
    assignment_date: str
    bus_id: str
    bus_number: Optional[str] = None
    driver_id: str
    driver_name: Optional[str] = None
    conductor_id: Optional[str]
    conductor_name: Optional[str] = None
    route_id: str
    route_number: Optional[str] = None
    scheduled_departure: Optional[str]
    is_active: bool
    notes: Optional[str]

    model_config = {"from_attributes": True}


class CreateTrackingKeyRequest(BaseModel):
    label: str
    depot_id: Optional[str] = None

    @field_validator("label")
    @classmethod
    def check_label(cls, v):
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Label too short")
        return v


class TrackingKeyResponse(BaseModel):
    id: str
    label: str
    key_prefix: str
    depot_id: Optional[str]
    depot_code: Optional[str] = None
    is_active: bool
    last_used_at: Optional[str]
    created_at: str


class TrackingKeyCreatedResponse(TrackingKeyResponse):
    api_key: str


class CsvImportRequest(BaseModel):
    csv_text: str

    @field_validator("csv_text")
    @classmethod
    def check_csv(cls, v):
        v = v.strip()
        if len(v) < 10:
            raise ValueError("CSV content too short")
        return v


class CsvImportResponse(BaseModel):
    success: bool
    created: int
    updated: int
    errors: list[str]


class UpdateBusAssignmentRequest(BaseModel):
    route_id: Optional[str] = None
    driver_id: Optional[str] = None
    conductor_id: Optional[str] = None
    gps_device_id: Optional[str] = None
    driver_name: Optional[str] = None
    conductor_name: Optional[str] = None
    conductor_mobile: Optional[str] = None

    @field_validator("gps_device_id")
    @classmethod
    def check_gps_device_id(cls, v):
        if v is not None:
            v = v.strip() or None
        return v

    @field_validator("conductor_mobile")
    @classmethod
    def check_conductor_mobile(cls, v):
        if v is not None:
            v = v.strip()
            if v and not re.fullmatch(r"[6-9]\d{9}", v):
                raise ValueError("Invalid conductor mobile number")
        return v


class CreateBusRequestExtended(BaseModel):
    bus_number: str
    registration_number: str
    bus_type: BusType = BusType.ORDINARY
    route_id: Optional[str] = None
    seating_capacity: int = 52
    standing_capacity: int = 20
    gps_device_id: Optional[str] = None
    driver_id: Optional[str] = None
    conductor_id: Optional[str] = None
    driver_name: Optional[str] = None
    conductor_name: Optional[str] = None
    conductor_mobile: Optional[str] = None

    @field_validator("bus_number", "registration_number")
    @classmethod
    def normalize_upper(cls, v):
        v = v.strip().upper()
        if len(v) < 4:
            raise ValueError("Value too short")
        return v

    @field_validator("gps_device_id")
    @classmethod
    def check_gps_device_id(cls, v):
        if v is not None:
            v = v.strip() or None
        return v

    @field_validator("conductor_mobile")
    @classmethod
    def check_conductor_mobile(cls, v):
        if v is not None:
            v = v.strip()
            if v and not re.fullmatch(r"[6-9]\d{9}", v):
                raise ValueError("Invalid conductor mobile number")
        return v
