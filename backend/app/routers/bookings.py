"""
backend/app/routers/bookings.py
================================
Bookings router for UNIreserve (P4: Gowtham Sai).

Endpoints:
  - POST /bookings                   : Submit a booking request (triggers validate rules & write audit log)
  - GET  /bookings/my                : Fetch current user's bookings with facility info & status timeline
  - GET  /bookings/{booking_id}/logs : Fetch chronological status audit logs for a booking
  - PUT  /bookings/{booking_id}/cancel  : Cancel a booking via stored function cancel_booking()
  - POST /bookings/{booking_id}/cancel  : Alias for frontend compatibility
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.database import get_db_cursor
from app.dependencies import get_current_user_id
from app.schemas.booking import (
    BookingActionResponse,
    BookingCreate,
    BookingResponse,
    StatusLogEntry,
)

router = APIRouter(prefix="/bookings", tags=["Bookings"])


def _fetch_logs_for_bookings(cur, booking_ids: List[int]) -> Dict[int, List[StatusLogEntry]]:
    """Fetches chronological BookingStatusLog entries for one or more booking IDs."""
    if not booking_ids:
        return {}

    cur.execute(
        """
        SELECT l.LogID, l.BookingID, l.OldStatus, l.NewStatus,
               l.ChangedByUserID, u.Name AS ChangedByName, l.ChangedAt
        FROM BookingStatusLog l
        LEFT JOIN Users u ON u.UserID = l.ChangedByUserID
        WHERE l.BookingID = ANY(%s)
        ORDER BY l.ChangedAt ASC, l.LogID ASC;
        """,
        (booking_ids,),
    )
    logs_by_booking: Dict[int, List[StatusLogEntry]] = {}
    for log in cur.fetchall():
        logs_by_booking.setdefault(log["bookingid"], []).append(
            StatusLogEntry(
                log_id=log["logid"],
                booking_id=log["bookingid"],
                old_status=log["oldstatus"],
                new_status=log["newstatus"],
                changed_by_user_id=log["changedbyuserid"],
                changed_by_name=log["changedbyname"],
                changed_at=log["changedat"],
            )
        )
    return logs_by_booking


def _build_booking_response(row: dict, logs: List[StatusLogEntry]) -> BookingResponse:
    """Maps a Booking + Facility query row into a BookingResponse."""
    return BookingResponse(
        booking_id=row["bookingid"],
        user_id=row["userid"],
        facility_id=row["facilityid"],
        facility_name=row.get("facilityname"),
        facility_location=row.get("facilitylocation"),
        facility_type=row.get("facilitytype"),
        booking_date=row["bookingdate"],
        start_time=row["starttime"],
        end_time=row["endtime"],
        status=row["status"],
        purpose=row["purpose"],
        created_at=row["createdat"],
        logs=logs,
        status_logs=logs,
    )


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: BookingCreate,
    user_id: int = Depends(get_current_user_id),
):
    """
    Submits a new booking request.
    Sets `app.current_user_id` before INSERT so `trg_booking_audit_log` records the acting user.
    Database triggers automatically enforce duration caps, availability, and advance windows.
    """
    with get_db_cursor(commit=True, user_id=user_id) as cur:
        cur.execute(
            "SELECT Name, Location, FacilityType, Status FROM Facility WHERE FacilityID = %s;",
            (payload.facility_id,),
        )
        fac = cur.fetchone()
        if not fac:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility not found")

        cur.execute(
            """
            INSERT INTO Booking (UserID, FacilityID, BookingDate, StartTime, EndTime, Status, Purpose)
            VALUES (%s, %s, %s, %s, %s, 'Pending', %s)
            RETURNING BookingID, UserID, FacilityID, BookingDate, StartTime, EndTime, Status, Purpose, CreatedAt;
            """,
            (
                user_id,
                payload.facility_id,
                payload.booking_date,
                payload.start_time,
                payload.end_time,
                payload.purpose,
            ),
        )
        row = dict(cur.fetchone())
        row["facilityname"] = fac["name"]
        row["facilitylocation"] = fac["location"]
        row["facilitytype"] = fac["facilitytype"]

        logs = _fetch_logs_for_bookings(cur, [row["bookingid"]]).get(row["bookingid"], [])
        return _build_booking_response(row, logs)


@router.get("/my", response_model=List[BookingResponse])
def get_my_bookings(
    user_id: int = Depends(get_current_user_id),
    status_filter: Optional[str] = Query(None),
    status_alias: Optional[str] = Query(None, alias="status"),
):
    """
    Retrieves the current user's bookings joined with Facility metadata and
    chronological BookingStatusLog entries for rendering the status timeline.
    """
    effective_status = status_filter or status_alias

    with get_db_cursor(commit=False) as cur:
        query = """
            SELECT b.BookingID, b.UserID, b.FacilityID, b.BookingDate, b.StartTime, b.EndTime,
                   b.Status, b.Purpose, b.CreatedAt,
                   f.Name AS FacilityName, f.Location AS FacilityLocation, f.FacilityType
            FROM Booking b
            JOIN Facility f ON f.FacilityID = b.FacilityID
            WHERE b.UserID = %s
        """
        params: list = [user_id]
        if effective_status:
            query += " AND b.Status = %s"
            params.append(effective_status)

        query += " ORDER BY b.BookingDate DESC, b.StartTime DESC;"
        cur.execute(query, tuple(params))
        bookings = cur.fetchall()

        if not bookings:
            return []

        booking_ids = [b["bookingid"] for b in bookings]
        logs_by_booking = _fetch_logs_for_bookings(cur, booking_ids)

        return [
            _build_booking_response(dict(b), logs_by_booking.get(b["bookingid"], []))
            for b in bookings
        ]


@router.get("/{booking_id}/logs", response_model=List[StatusLogEntry])
def get_booking_logs(
    booking_id: int,
    user_id: int = Depends(get_current_user_id),
):
    """
    Returns chronological status audit log entries for a booking.
    Accessible to the booking owner or an Admin.
    """
    with get_db_cursor(commit=False) as cur:
        cur.execute("SELECT UserID FROM Booking WHERE BookingID = %s;", (booking_id,))
        booking = cur.fetchone()
        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

        if booking["userid"] != user_id:
            cur.execute("SELECT Role FROM Users WHERE UserID = %s;", (user_id,))
            actor = cur.fetchone()
            if not actor or actor["role"] != "Admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view logs for this booking",
                )

        return _fetch_logs_for_bookings(cur, [booking_id]).get(booking_id, [])


@router.put("/{booking_id}/cancel", response_model=BookingActionResponse)
@router.post("/{booking_id}/cancel", response_model=BookingActionResponse)
def cancel_booking_endpoint(
    booking_id: int,
    user_id: int = Depends(get_current_user_id),
):
    """
    Cancels a booking using the PostgreSQL stored procedure cancel_booking(p_booking_id, p_user_id).
    Sets `app.current_user_id` before calling `cancel_booking` and returns the updated booking row.
    """
    with get_db_cursor(commit=True, user_id=user_id) as cur:
        cur.execute("SELECT cancel_booking(%s, %s);", (booking_id, user_id))
        cur.execute(
            """
            SELECT b.BookingID, b.UserID, b.FacilityID, b.BookingDate, b.StartTime, b.EndTime,
                   b.Status, b.Purpose, b.CreatedAt,
                   f.Name AS FacilityName, f.Location AS FacilityLocation, f.FacilityType
            FROM Booking b
            JOIN Facility f ON f.FacilityID = b.FacilityID
            WHERE b.BookingID = %s;
            """,
            (booking_id,),
        )
        row = cur.fetchone()

        return BookingActionResponse(
            booking_id=row["bookingid"],
            status=row["status"],
            message="Booking cancelled successfully",
            user_id=row["userid"],
            facility_id=row["facilityid"],
            facility_name=row["facilityname"],
            facility_location=row["facilitylocation"],
            facility_type=row["facilitytype"],
            booking_date=row["bookingdate"],
            start_time=row["starttime"],
            end_time=row["endtime"],
            purpose=row["purpose"],
            created_at=row["createdat"],
        )
