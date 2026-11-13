"""
backend/app/routers/admin.py
=============================
Admin workflows & analytics router for UNIreserve (P4: Gowtham Sai).

All endpoints require the Admin role (`require_admin_user`).

Endpoints:
  - GET    /admin/bookings/pending          : Approval queue joined with Users & Facility
  - PUT    /admin/bookings/{id}/confirm     : Confirm pending booking (fires auto-reject & audit triggers)
  - PUT    /admin/bookings/{id}/reject      : Reject pending booking (fires audit trigger)
  - GET    /admin/analytics                 : Views + CTEs + GROUP BY dashboard analytics
  - GET    /admin/holidays                  : List holidays
  - POST   /admin/holidays                  : Create holiday
  - DELETE /admin/holidays/{holiday_id}     : Delete holiday
  - GET    /admin/maintenance               : List maintenance windows
  - POST   /admin/maintenance               : Create maintenance window
  - DELETE /admin/maintenance/{schedule_id} : Delete maintenance window
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db_cursor
from app.dependencies import require_admin_user
from app.schemas.admin import (
    AnalyticsOverview,
    FacilityWeeklyStat,
    HolidayCreate,
    HolidayResponse,
    MaintenanceCreate,
    MaintenanceResponse,
    PendingBookingResponse,
)
from app.schemas.booking import BookingActionResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


# ---------------------------------------------------------------------------
# Approval Queue
# ---------------------------------------------------------------------------

@router.get("/bookings/pending", response_model=List[PendingBookingResponse])
def list_pending_bookings(admin_id: int = Depends(require_admin_user)):
    """
    Returns all pending bookings awaiting administrative approval, joined with
    Users and Facility details, ordered by BookingDate ASC, StartTime ASC.
    """
    with get_db_cursor(commit=False) as cur:
        cur.execute(
            """
            SELECT b.BookingID, b.UserID, u.Name AS UserName, u.Email AS UserEmail, u.Role AS UserRole,
                   b.FacilityID, f.Name AS FacilityName, f.Location AS FacilityLocation, f.FacilityType,
                   b.BookingDate, b.StartTime, b.EndTime, b.Status, b.Purpose, b.CreatedAt
            FROM Booking b
            JOIN Users u ON u.UserID = b.UserID
            JOIN Facility f ON f.FacilityID = b.FacilityID
            WHERE b.Status = 'Pending'
            ORDER BY b.BookingDate ASC, b.StartTime ASC;
            """
        )
        return [
            PendingBookingResponse(
                booking_id=r["bookingid"],
                user_id=r["userid"],
                user_name=r["username"],
                user_email=r["useremail"],
                user_role=r["userrole"],
                facility_id=r["facilityid"],
                facility_name=r["facilityname"],
                facility_location=r["facilitylocation"],
                facility_type=r["facilitytype"],
                booking_date=r["bookingdate"],
                start_time=r["starttime"],
                end_time=r["endtime"],
                status=r["status"],
                purpose=r["purpose"],
                created_at=r["createdat"],
            )
            for r in cur.fetchall()
        ]


def _transition_pending_booking(
    booking_id: int,
    admin_id: int,
    target_status: str,
    message: str,
) -> BookingActionResponse:
    """
    Transitions a Pending booking to `target_status` ('Confirmed' or 'Rejected')
    with `app.current_user_id` set to `admin_id` so audit triggers record the admin.
    """
    verb = "confirm" if target_status == "Confirmed" else "reject"
    with get_db_cursor(commit=True, user_id=admin_id) as cur:
        cur.execute("SELECT Status FROM Booking WHERE BookingID = %s FOR UPDATE;", (booking_id,))
        existing = cur.fetchone()
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
        if existing["status"] != "Pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot {verb} booking in '{existing['status']}' state",
            )

        cur.execute(
            """
            UPDATE Booking
               SET Status = %s
             WHERE BookingID = %s AND Status = 'Pending'
            RETURNING BookingID, UserID, FacilityID, BookingDate, StartTime, EndTime, Status, Purpose, CreatedAt;
            """,
            (target_status, booking_id),
        )
        updated = cur.fetchone()
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot {verb} booking; it is no longer Pending",
            )

        return BookingActionResponse(
            booking_id=updated["bookingid"],
            status=updated["status"],
            message=message,
            user_id=updated["userid"],
            facility_id=updated["facilityid"],
            booking_date=updated["bookingdate"],
            start_time=updated["starttime"],
            end_time=updated["endtime"],
            purpose=updated["purpose"],
            created_at=updated["createdat"],
        )


@router.put("/bookings/{booking_id}/confirm", response_model=BookingActionResponse)
def confirm_booking(
    booking_id: int,
    admin_id: int = Depends(require_admin_user),
):
    """
    Confirms a pending booking request.
    `trg_booking_auto_reject` automatically rejects overlapping pending bookings
    and `trg_booking_audit_log` logs all changes with `ChangedByUserID = admin_id`.
    """
    return _transition_pending_booking(
        booking_id=booking_id,
        admin_id=admin_id,
        target_status="Confirmed",
        message="Booking confirmed; overlapping pending bookings auto-rejected.",
    )


@router.put("/bookings/{booking_id}/reject", response_model=BookingActionResponse)
def reject_booking(
    booking_id: int,
    admin_id: int = Depends(require_admin_user),
):
    """
    Rejects a pending booking request and logs the change with `ChangedByUserID = admin_id`.
    """
    return _transition_pending_booking(
        booking_id=booking_id,
        admin_id=admin_id,
        target_status="Rejected",
        message="Booking rejected successfully.",
    )


# ---------------------------------------------------------------------------
# Analytics & Reporting
# ---------------------------------------------------------------------------

@router.get("/analytics", response_model=AnalyticsOverview)
def get_analytics(admin_id: int = Depends(require_admin_user)):
    """
    Retrieves system analytics using database views (`booking_summary_view`,
    `facility_availability_view`), CTEs, and `GROUP BY` aggregations.
    """
    with get_db_cursor(commit=False) as cur:
        # 1. Weekly summary from booking_summary_view
        cur.execute(
            """
            SELECT FacilityID, FacilityName, WeekStart, TotalRequests,
                   Confirmed, Pending, Rejected, Cancelled, BookedHours
            FROM booking_summary_view
            ORDER BY WeekStart DESC, TotalRequests DESC;
            """
        )
        weekly_summary = [
            FacilityWeeklyStat(
                facility_id=r["facilityid"],
                facility_name=r["facilityname"],
                week_start=r["weekstart"],
                total_requests=r["totalrequests"],
                confirmed=r["confirmed"],
                pending=r["pending"],
                rejected=r["rejected"],
                cancelled=r["cancelled"],
                booked_hours=float(r["bookedhours"]),
            )
            for r in cur.fetchall()
        ]

        # 2. Overall counts by booking status
        cur.execute("SELECT Status, COUNT(*) AS count FROM Booking GROUP BY Status;")
        status_breakdown = {r["status"]: r["count"] for r in cur.fetchall()}

        # 3. Bookings breakdown by user role
        cur.execute(
            """
            SELECT u.Role, COUNT(b.BookingID) AS count
            FROM Booking b
            JOIN Users u ON u.UserID = b.UserID
            GROUP BY u.Role;
            """
        )
        role_breakdown = {r["role"]: r["count"] for r in cur.fetchall()}

        # 4. Top facilities by total bookings & confirmed utilization (CTE)
        cur.execute(
            """
            WITH FacilityStats AS (
                SELECT b.FacilityID AS facility_id,
                       f.Name AS name,
                       f.FacilityType AS facility_type,
                       COUNT(*) AS total_bookings,
                       COUNT(*) FILTER (WHERE b.Status = 'Confirmed') AS confirmed_count,
                       COALESCE(
                           ROUND(
                               SUM(EXTRACT(EPOCH FROM (b.EndTime - b.StartTime)) / 3600.0)
                               FILTER (WHERE b.Status IN ('Confirmed', 'Completed')),
                               2
                           ),
                           0
                       )::float AS booked_hours
                FROM Booking b
                JOIN Facility f ON f.FacilityID = b.FacilityID
                GROUP BY b.FacilityID, f.Name, f.FacilityType
            )
            SELECT * FROM FacilityStats
            ORDER BY total_bookings DESC, facility_id ASC
            LIMIT 5;
            """
        )
        top_facilities = [dict(r) for r in cur.fetchall()]

        # 5. Peak booking start hours (CTE)
        cur.execute(
            """
            WITH HourlyCounts AS (
                SELECT EXTRACT(HOUR FROM StartTime)::int AS hour,
                       COUNT(*) AS total_bookings,
                       COUNT(*) FILTER (WHERE Status = 'Confirmed') AS confirmed_bookings
                FROM Booking
                GROUP BY EXTRACT(HOUR FROM StartTime)::int
            )
            SELECT hour,
                   LPAD(hour::text, 2, '0') || ':00' AS time_slot,
                   total_bookings,
                   confirmed_bookings
            FROM HourlyCounts
            ORDER BY total_bookings DESC, hour ASC
            LIMIT 10;
            """
        )
        peak_hours = [dict(r) for r in cur.fetchall()]

        # 6. Upcoming slot load by facility type from facility_availability_view (CTE)
        cur.execute(
            """
            WITH UpcomingLoad AS (
                SELECT FacilityType AS facility_type,
                       COUNT(DISTINCT FacilityID) FILTER (WHERE FacilityStatus = 'Active') AS active_facilities,
                       COUNT(DISTINCT FacilityID) FILTER (WHERE FacilityStatus = 'Under Maintenance') AS maintenance_facilities,
                       COUNT(*) FILTER (WHERE BookingStatus = 'Confirmed') AS upcoming_confirmed_slots,
                       COUNT(*) FILTER (WHERE BookingStatus = 'Pending') AS upcoming_pending_slots
                FROM facility_availability_view
                GROUP BY FacilityType
            )
            SELECT * FROM UpcomingLoad
            ORDER BY facility_type ASC;
            """
        )
        upcoming_availability = [dict(r) for r in cur.fetchall()]

        return AnalyticsOverview(
            summary=weekly_summary,
            weekly_summary=weekly_summary,
            status_counts=status_breakdown,
            status_breakdown=status_breakdown,
            role_breakdown=role_breakdown,
            top_facilities=top_facilities,
            peak_hours=peak_hours,
            upcoming_availability=upcoming_availability,
        )


# ---------------------------------------------------------------------------
# Holidays Management
# ---------------------------------------------------------------------------

@router.get("/holidays", response_model=List[HolidayResponse])
def list_holidays(admin_id: int = Depends(require_admin_user)):
    with get_db_cursor(commit=False) as cur:
        cur.execute("SELECT HolidayID, HolidayDate, Description FROM Holiday ORDER BY HolidayDate ASC;")
        return [
            HolidayResponse(
                holiday_id=r["holidayid"],
                holiday_date=r["holidaydate"],
                description=r["description"],
            )
            for r in cur.fetchall()
        ]


@router.post("/holidays", response_model=HolidayResponse, status_code=status.HTTP_201_CREATED)
def create_holiday(payload: HolidayCreate, admin_id: int = Depends(require_admin_user)):
    with get_db_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO Holiday (HolidayDate, Description) VALUES (%s, %s) RETURNING HolidayID, HolidayDate, Description;",
            (payload.holiday_date, payload.description),
        )
        r = cur.fetchone()
        return HolidayResponse(
            holiday_id=r["holidayid"],
            holiday_date=r["holidaydate"],
            description=r["description"],
        )


@router.delete("/holidays/{holiday_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_holiday(holiday_id: int, admin_id: int = Depends(require_admin_user)):
    with get_db_cursor(commit=True) as cur:
        cur.execute("DELETE FROM Holiday WHERE HolidayID = %s RETURNING HolidayID;", (holiday_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holiday not found")
        return None


# ---------------------------------------------------------------------------
# Maintenance Management
# ---------------------------------------------------------------------------

@router.get("/maintenance", response_model=List[MaintenanceResponse])
def list_maintenance(admin_id: int = Depends(require_admin_user)):
    with get_db_cursor(commit=False) as cur:
        cur.execute(
            """
            SELECT m.ScheduleID, m.FacilityID, f.Name AS FacilityName,
                   m.StartDate, m.EndDate, m.StartTime, m.EndTime, m.Description
            FROM MaintenanceSchedule m
            JOIN Facility f ON f.FacilityID = m.FacilityID
            ORDER BY m.StartDate DESC;
            """
        )
        return [
            MaintenanceResponse(
                schedule_id=r["scheduleid"],
                facility_id=r["facilityid"],
                facility_name=r["facilityname"],
                start_date=r["startdate"],
                end_date=r["enddate"],
                start_time=r["starttime"],
                end_time=r["endtime"],
                description=r["description"],
            )
            for r in cur.fetchall()
        ]


@router.post("/maintenance", response_model=MaintenanceResponse, status_code=status.HTTP_201_CREATED)
def create_maintenance(payload: MaintenanceCreate, admin_id: int = Depends(require_admin_user)):
    if payload.end_time <= payload.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maintenance end_time must be after start_time",
        )

    with get_db_cursor(commit=True) as cur:
        cur.execute("SELECT Name FROM Facility WHERE FacilityID = %s;", (payload.facility_id,))
        fac = cur.fetchone()
        if not fac:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility not found")

        cur.execute(
            """
            INSERT INTO MaintenanceSchedule (FacilityID, StartDate, EndDate, StartTime, EndTime, Description)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING ScheduleID, FacilityID, StartDate, EndDate, StartTime, EndTime, Description;
            """,
            (
                payload.facility_id,
                payload.start_date,
                payload.end_date,
                payload.start_time,
                payload.end_time,
                payload.description,
            ),
        )
        r = cur.fetchone()
        return MaintenanceResponse(
            schedule_id=r["scheduleid"],
            facility_id=r["facilityid"],
            facility_name=fac["name"],
            start_date=r["startdate"],
            end_date=r["enddate"],
            start_time=r["starttime"],
            end_time=r["endtime"],
            description=r["description"],
        )


@router.delete("/maintenance/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_maintenance(schedule_id: int, admin_id: int = Depends(require_admin_user)):
    with get_db_cursor(commit=True) as cur:
        cur.execute("DELETE FROM MaintenanceSchedule WHERE ScheduleID = %s RETURNING ScheduleID;", (schedule_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance schedule not found")
        return None
