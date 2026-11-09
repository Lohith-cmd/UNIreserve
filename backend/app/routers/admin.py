from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db_cursor
from app.dependencies import require_admin_user
from app.schemas.booking import BookingActionResponse
from app.schemas.admin import (
    HolidayCreate,
    HolidayResponse,
    MaintenanceCreate,
    MaintenanceResponse,
    FacilityWeeklyStat,
    AnalyticsOverview,
)

router = APIRouter(prefix="/admin", tags=["Admin"])


# --- Approval Queue ---

@router.get("/bookings/pending")
def list_pending_bookings(admin_id: int = Depends(require_admin_user)):
    """
    Returns all pending bookings awaiting administrative approval.
    """
    with get_db_cursor(commit=False) as cur:
        query = """
            SELECT b.BookingID, b.UserID, u.Name AS UserName, u.Email AS UserEmail, u.Role AS UserRole,
                   b.FacilityID, f.Name AS FacilityName, f.FacilityType,
                   b.BookingDate, b.StartTime, b.EndTime, b.Purpose, b.CreatedAt
            FROM Booking b
            JOIN Users u ON u.UserID = b.UserID
            JOIN Facility f ON f.FacilityID = b.FacilityID
            WHERE b.Status = 'Pending'
            ORDER BY b.BookingDate ASC, b.StartTime ASC;
        """
        cur.execute(query)
        return cur.fetchall()


@router.put("/bookings/{booking_id}/confirm", response_model=BookingActionResponse)
def confirm_booking(
    booking_id: int,
    admin_id: int = Depends(require_admin_user),
):
    """
    Confirms a booking request.
    Firing the database trigger trg_booking_auto_reject will automatically
    reject any overlapping pending bookings for this facility/time slot.
    """
    with get_db_cursor(commit=True, user_id=admin_id) as cur:
        cur.execute("SELECT Status FROM Booking WHERE BookingID = %s FOR UPDATE;", (booking_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Booking not found")
        if row["status"] != "Pending":
            raise HTTPException(status_code=400, detail=f"Cannot confirm booking in '{row['status']}' state")

        cur.execute("UPDATE Booking SET Status = 'Confirmed' WHERE BookingID = %s;", (booking_id,))
        return BookingActionResponse(
            booking_id=booking_id,
            status="Confirmed",
            message="Booking confirmed; overlapping pending bookings auto-rejected.",
        )


@router.put("/bookings/{booking_id}/reject", response_model=BookingActionResponse)
def reject_booking(
    booking_id: int,
    admin_id: int = Depends(require_admin_user),
):
    """
    Rejects a booking request.
    """
    with get_db_cursor(commit=True, user_id=admin_id) as cur:
        cur.execute("SELECT Status FROM Booking WHERE BookingID = %s FOR UPDATE;", (booking_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Booking not found")
        if row["status"] != "Pending":
            raise HTTPException(status_code=400, detail=f"Cannot reject booking in '{row['status']}' state")

        cur.execute("UPDATE Booking SET Status = 'Rejected' WHERE BookingID = %s;", (booking_id,))
        return BookingActionResponse(
            booking_id=booking_id,
            status="Rejected",
            message="Booking rejected successfully.",
        )


# --- Analytics & Reporting ---

@router.get("/analytics", response_model=AnalyticsOverview)
def get_analytics(admin_id: int = Depends(require_admin_user)):
    """
    Retrieves system analytics using the booking_summary_view and aggregate CTEs.
    """
    with get_db_cursor(commit=False) as cur:
        # 1. Weekly summary view
        cur.execute("""
            SELECT FacilityID, FacilityName, WeekStart, TotalRequests,
                   Confirmed, Pending, Rejected, Cancelled, BookedHours
            FROM booking_summary_view
            ORDER BY WeekStart DESC, TotalRequests DESC;
        """)
        summary_rows = cur.fetchall()
        summary = [
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
            for r in summary_rows
        ]

        # 2. Overall counts by status
        cur.execute("SELECT Status, COUNT(*) as count FROM Booking GROUP BY Status;")
        status_counts = {r["status"]: r["count"] for r in cur.fetchall()}

        # 3. Top facilities by utilization / total requests (CTE)
        cur.execute("""
            WITH FacilityStats AS (
                SELECT b.FacilityID, f.Name, f.FacilityType,
                       COUNT(*) AS TotalBookings,
                       COUNT(*) FILTER (WHERE b.Status = 'Confirmed') AS ConfirmedCount
                FROM Booking b
                JOIN Facility f ON f.FacilityID = b.FacilityID
                GROUP BY b.FacilityID, f.Name, f.FacilityType
            )
            SELECT * FROM FacilityStats ORDER BY TotalBookings DESC LIMIT 5;
        """)
        top_facilities = cur.fetchall()

        return AnalyticsOverview(
            summary=summary,
            status_counts=status_counts,
            top_facilities=top_facilities,
        )


# --- Holidays Management ---

@router.get("/holidays", response_model=List[HolidayResponse])
def list_holidays(admin_id: int = Depends(require_admin_user)):
    with get_db_cursor(commit=False) as cur:
        cur.execute("SELECT HolidayID, HolidayDate, Description FROM Holiday ORDER BY HolidayDate ASC;")
        rows = cur.fetchall()
        return [HolidayResponse(holiday_id=r["holidayid"], holiday_date=r["holidaydate"], description=r["description"]) for r in rows]


@router.post("/holidays", response_model=HolidayResponse, status_code=status.HTTP_201_CREATED)
def create_holiday(payload: HolidayCreate, admin_id: int = Depends(require_admin_user)):
    with get_db_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO Holiday (HolidayDate, Description) VALUES (%s, %s) RETURNING HolidayID, HolidayDate, Description;",
            (payload.holiday_date, payload.description),
        )
        r = cur.fetchone()
        return HolidayResponse(holiday_id=r["holidayid"], holiday_date=r["holidaydate"], description=r["description"])


@router.delete("/holidays/{holiday_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_holiday(holiday_id: int, admin_id: int = Depends(require_admin_user)):
    with get_db_cursor(commit=True) as cur:
        cur.execute("DELETE FROM Holiday WHERE HolidayID = %s RETURNING HolidayID;", (holiday_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Holiday not found")
        return None


# --- Maintenance Management ---

@router.get("/maintenance", response_model=List[MaintenanceResponse])
def list_maintenance(admin_id: int = Depends(require_admin_user)):
    with get_db_cursor(commit=False) as cur:
        cur.execute("""
            SELECT m.ScheduleID, m.FacilityID, f.Name AS FacilityName,
                   m.StartDate, m.EndDate, m.StartTime, m.EndTime, m.Description
            FROM MaintenanceSchedule m
            JOIN Facility f ON f.FacilityID = m.FacilityID
            ORDER BY m.StartDate DESC;
        """)
        rows = cur.fetchall()
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
            for r in rows
        ]


@router.post("/maintenance", response_model=MaintenanceResponse, status_code=status.HTTP_201_CREATED)
def create_maintenance(payload: MaintenanceCreate, admin_id: int = Depends(require_admin_user)):
    with get_db_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO MaintenanceSchedule (FacilityID, StartDate, EndDate, StartTime, EndTime, Description)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING ScheduleID, FacilityID, StartDate, EndDate, StartTime, EndTime, Description;
            """,
            (payload.facility_id, payload.start_date, payload.end_date, payload.start_time, payload.end_time, payload.description),
        )
        r = cur.fetchone()
        return MaintenanceResponse(
            schedule_id=r["scheduleid"],
            facility_id=r["facilityid"],
            facility_name=None,
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
            raise HTTPException(status_code=404, detail="Maintenance schedule not found")
        return None

