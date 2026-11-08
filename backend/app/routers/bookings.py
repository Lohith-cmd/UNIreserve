from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db_cursor
from app.dependencies import get_current_user_id
from app.schemas.booking import (
    BookingCreate,
    BookingResponse,
    BookingActionResponse,
    StatusLogEntry,
)

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: BookingCreate,
    user_id: int = Depends(get_current_user_id),
):
    """
    Submits a new booking request.
    Database triggers automatically enforce:
    - Minimum duration & role duration caps (Student max 1h, Faculty max 1h sports / 3h classroom)
    - Advance booking windows (Student 7d, Faculty 14d) and no past dates
    - Classroom opening hours and sports venue hours
    - Maintenance schedule conflicts
    """
    with get_db_cursor(commit=True, user_id=user_id) as cur:
        # Check facility exists
        cur.execute("SELECT Name, FacilityType, Status FROM Facility WHERE FacilityID = %s;", (payload.facility_id,))
        fac = cur.fetchone()
        if not fac:
            raise HTTPException(status_code=404, detail="Facility not found")

        # Insert booking (triggers will fire and raise exceptions if rules are violated)
        insert_query = """
            INSERT INTO Booking (UserID, FacilityID, BookingDate, StartTime, EndTime, Status, Purpose)
            VALUES (%s, %s, %s, %s, %s, 'Pending', %s)
            RETURNING BookingID, UserID, FacilityID, BookingDate, StartTime, EndTime, Status, Purpose, CreatedAt;
        """
        cur.execute(
            insert_query,
            (user_id, payload.facility_id, payload.booking_date, payload.start_time, payload.end_time, payload.purpose),
        )
        row = cur.fetchone()

        return BookingResponse(
            booking_id=row["bookingid"],
            user_id=row["userid"],
            facility_id=row["facilityid"],
            facility_name=fac["name"],
            facility_type=fac["facilitytype"],
            booking_date=row["bookingdate"],
            start_time=row["starttime"],
            end_time=row["endtime"],
            status=row["status"],
            purpose=row["purpose"],
            created_at=row["createdat"],
            logs=[],
        )


@router.get("/my", response_model=List[BookingResponse])
def get_my_bookings(
    user_id: int = Depends(get_current_user_id),
    status_filter: Optional[str] = None,
):
    """
    Retrieves the current user's bookings with facility information and status timeline.
    """
    with get_db_cursor(commit=False) as cur:
        query = """
            SELECT b.BookingID, b.UserID, b.FacilityID, b.BookingDate, b.StartTime, b.EndTime,
                   b.Status, b.Purpose, b.CreatedAt,
                   f.Name AS FacilityName, f.FacilityType
            FROM Booking b
            JOIN Facility f ON f.FacilityID = b.FacilityID
            WHERE b.UserID = %s
        """
        params = [user_id]
        if status_filter:
            query += " AND b.Status = %s"
            params.append(status_filter)

        query += " ORDER BY b.BookingDate DESC, b.StartTime DESC;"
        cur.execute(query, tuple(params))
        bookings = cur.fetchall()

        if not bookings:
            return []

        booking_ids = [b["bookingid"] for b in bookings]

        # Fetch status audit logs for timeline
        cur.execute(
            """
            SELECT LogID, BookingID, OldStatus, NewStatus, ChangedByUserID, ChangedAt
            FROM BookingStatusLog
            WHERE BookingID = ANY(%s)
            ORDER BY ChangedAt ASC;
            """,
            (booking_ids,),
        )
        all_logs = cur.fetchall()

        logs_by_booking = {}
        for log in all_logs:
            logs_by_booking.setdefault(log["bookingid"], []).append(
                StatusLogEntry(
                    log_id=log["logid"],
                    booking_id=log["bookingid"],
                    old_status=log["oldstatus"],
                    new_status=log["newstatus"],
                    changed_by_user_id=log["changedbyuserid"],
                    changed_at=log["changedat"],
                )
            )

        results = []
        for b in bookings:
            results.append(
                BookingResponse(
                    booking_id=b["bookingid"],
                    user_id=b["userid"],
                    facility_id=b["facilityid"],
                    facility_name=b["facilityname"],
                    facility_type=b["facilitytype"],
                    booking_date=b["bookingdate"],
                    start_time=b["starttime"],
                    end_time=b["endtime"],
                    status=b["status"],
                    purpose=b["purpose"],
                    created_at=b["createdat"],
                    logs=logs_by_booking.get(b["bookingid"], []),
                )
            )
        return results


@router.put("/{booking_id}/cancel", response_model=BookingActionResponse)
def cancel_booking_endpoint(
    booking_id: int,
    user_id: int = Depends(get_current_user_id),
):
    """
    Cancels a booking using the PostgreSQL stored procedure cancel_booking(p_booking_id, p_user_id).
    Enforces booking ownership and the minimum 2-hour cancellation cutoff.
    """
    with get_db_cursor(commit=True, user_id=user_id) as cur:
        cur.execute("SELECT cancel_booking(%s, %s);", (booking_id, user_id))
        return BookingActionResponse(
            booking_id=booking_id,
            status="Cancelled",
            message="Booking cancelled successfully",
        )

