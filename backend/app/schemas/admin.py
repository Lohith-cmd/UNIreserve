from datetime import date, time
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


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
    status_counts: Dict[str, int]
    top_facilities: List[Dict[str, Any]]

