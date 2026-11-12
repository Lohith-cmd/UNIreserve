"""
backend/app/schemas.py
======================
Unified Pydantic v2 schemas for UNIreserve.

Enums mirror the PostgreSQL ENUM types defined in schema.sql.
All user_id fields use Python int (arbitrary precision) which natively
handles 11-digit BIGINT values from the Users table (BIGSERIAL).
"""

from datetime import date, datetime, time
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums (mirror PostgreSQL ENUM types)
# ---------------------------------------------------------------------------

class UserRole(str, Enum):
    Student = "Student"
    Faculty = "Faculty"
    Admin = "Admin"


class FacilityType(str, Enum):
    Sports = "Sports"
    Classroom = "Classroom"
    Other = "Other"


class FacilityStatus(str, Enum):
    Active = "Active"
    Maintenance = "Under Maintenance"


class BookingStatus(str, Enum):
    Pending = "Pending"
    Confirmed = "Confirmed"
    Rejected = "Rejected"
    Cancelled = "Cancelled"
    Completed = "Completed"


class IndoorOutdoor(str, Enum):
    Indoor = "Indoor"
    Outdoor = "Outdoor"


# ---------------------------------------------------------------------------
# Auth / User schemas
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=150)
    password: str


class StudentRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=3, max_length=150)
    password: str = Field(..., min_length=6)
    phone: Optional[str] = Field(None, max_length=20)
    bits_id: str = Field(..., min_length=12, max_length=13)
    department: Optional[str] = None
    year: int = Field(..., ge=2020, le=2024)


class FacultyRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=3, max_length=150)
    password: str = Field(..., min_length=6)
    phone: Optional[str] = Field(None, max_length=20)
    employee_id: str = Field(..., min_length=3, max_length=20)
    department: Optional[str] = None
    designation: Optional[str] = None


class UserProfileResponse(BaseModel):
    """Full user profile returned by /auth/me and embedded in TokenResponse."""

    user_id: int  # BIGINT -> Python int is unbounded; handles 11-digit IDs
    name: str
    email: str
    role: str
    phone: Optional[str] = None
    bits_id: Optional[str] = None
    department: Optional[str] = None
    year: Optional[int] = None
    employee_id: Optional[str] = None
    designation: Optional[str] = None
    admin_level: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfileResponse


# ---------------------------------------------------------------------------
# Facility schemas
# ---------------------------------------------------------------------------

class FacilityResponse(BaseModel):
    """Full facility record returned by GET /facilities."""

    facility_id: int
    name: str
    location: Optional[str] = None
    facility_type: str
    status: str
    venue_type: Optional[str] = None
    surface: Optional[str] = None
    indoor_outdoor: Optional[str] = None
    building_name: Optional[str] = None
    room_number: Optional[str] = None
    room_type: Optional[str] = None
    capacity: Optional[int] = None
    has_projector: Optional[bool] = None
    has_ac: Optional[bool] = None
    venue_category: Optional[str] = None


class FacilityAvailabilityFilter(BaseModel):
    """Query parameters for GET /facilities/available."""

    date: date
    start_time: time
    end_time: time
    facility_type: Optional[FacilityType] = None


class AvailableFacilityResponse(FacilityResponse):
    """Availability result row also carries pending demand count."""

    pending_requests: int = 0


# ---------------------------------------------------------------------------
# Booking schemas
# ---------------------------------------------------------------------------

class StatusLogEntry(BaseModel):
    """Audit trail entry for a booking status change."""

    log_id: int
    booking_id: int
    old_status: Optional[str] = None
    new_status: str
    changed_by_user_id: Optional[int] = None  # BIGINT -> Python int
    changed_by_name: Optional[str] = None
    changed_at: datetime


class BookingCreate(BaseModel):
    facility_id: int
    booking_date: date
    start_time: time
    end_time: time
    purpose: Optional[str] = Field(None, max_length=255)


class BookingResponse(BaseModel):
    """Booking record returned to callers."""

    booking_id: int
    user_id: int  # BIGINT -> Python int
    facility_id: int
    facility_name: Optional[str] = None
    facility_location: Optional[str] = None
    facility_type: Optional[str] = None
    booking_date: date
    start_time: time
    end_time: time
    status: str
    purpose: Optional[str] = None
    created_at: datetime
    logs: List[StatusLogEntry] = Field(default_factory=list)
    status_logs: List[StatusLogEntry] = Field(default_factory=list)


class BookingActionResponse(BaseModel):
    booking_id: int
    status: str
    message: str
    user_id: Optional[int] = None
    facility_id: Optional[int] = None
    facility_name: Optional[str] = None
    facility_location: Optional[str] = None
    facility_type: Optional[str] = None
    booking_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    purpose: Optional[str] = None
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Admin schemas
# ---------------------------------------------------------------------------

class PendingBookingResponse(BaseModel):
    """Pending booking item shown in the Admin approval queue."""

    booking_id: int
    user_id: int
    user_name: str
    user_email: str
    user_role: str
    facility_id: int
    facility_name: str
    facility_location: Optional[str] = None
    facility_type: str
    booking_date: date
    start_time: time
    end_time: time
    status: str = "Pending"
    purpose: Optional[str] = None
    created_at: datetime


class HolidayCreate(BaseModel):
    holiday_date: date
    description: Optional[str] = Field(None, max_length=255)


class HolidayResponse(BaseModel):
    holiday_id: int
    holiday_date: date
    description: Optional[str] = None


class MaintenanceCreate(BaseModel):
    facility_id: int
    start_date: date
    end_date: date
    start_time: time
    end_time: time
    description: Optional[str] = Field(None, max_length=255)


class MaintenanceResponse(BaseModel):
    schedule_id: int
    facility_id: int
    facility_name: Optional[str] = None
    start_date: date
    end_date: date
    start_time: time
    end_time: time
    description: Optional[str] = None


class FacilityWeeklyStat(BaseModel):
    facility_id: int
    facility_name: str
    week_start: date
    total_requests: int
    confirmed: int
    pending: int
    rejected: int
    cancelled: int
    booked_hours: float


class AnalyticsOverview(BaseModel):
    summary: List[FacilityWeeklyStat]
    weekly_summary: List[FacilityWeeklyStat]
    status_counts: Dict[str, int]
    status_breakdown: Dict[str, int]
    role_breakdown: Dict[str, int]
    top_facilities: List[Dict[str, Any]]
    peak_hours: List[Dict[str, Any]]
    upcoming_availability: List[Dict[str, Any]]
