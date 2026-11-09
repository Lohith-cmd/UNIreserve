from datetime import date, time, datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class StatusLogEntry(BaseModel):
    log_id: int
    booking_id: int
    old_status: Optional[str] = None
    new_status: str
    changed_by_user_id: Optional[int] = None
    changed_at: datetime


class BookingCreate(BaseModel):
    facility_id: int
    booking_date: date
    start_time: time
    end_time: time
    purpose: Optional[str] = Field(None, max_length=255)


class BookingResponse(BaseModel):
    booking_id: int
    user_id: int
    facility_id: int
    facility_name: Optional[str] = None
    facility_type: Optional[str] = None
    booking_date: date
    start_time: time
    end_time: time
    status: str
    purpose: Optional[str] = None
    created_at: datetime
    logs: Optional[List[StatusLogEntry]] = None


class BookingActionResponse(BaseModel):
    booking_id: int
    status: str
    message: str

