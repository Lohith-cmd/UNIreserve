from datetime import date, datetime, time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PendingBookingResponse(BaseModel):
    """Pending booking item shown in the Admin approval queue."""

    booking_id: int
    user_id: int  # BIGINT in DB; Python int handles 11-digit IDs
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
