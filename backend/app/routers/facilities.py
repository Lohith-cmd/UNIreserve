from datetime import date, time
from typing import Optional, List
from fastapi import APIRouter, Query
from app.database import get_db_cursor

router = APIRouter(prefix="/facilities", tags=["Facilities"])


@router.get("")
def list_facilities(facility_type: Optional[str] = None, status: Optional[str] = None):
    """
    Lists facilities with optional filters for type and status.
    """
    with get_db_cursor(commit=False) as cur:
        query = """
            SELECT f.FacilityID, f.Name, f.Location, f.FacilityType, f.Status,
                   s.VenueType, s.Surface, s.IndoorOutdoor,
                   c.BuildingName, c.RoomNumber, c.Capacity, c.HasProjector, c.HasAC, c.RoomType
            FROM Facility f
            LEFT JOIN SportsVenue s ON s.FacilityID = f.FacilityID
            LEFT JOIN Classroom c ON c.FacilityID = f.FacilityID
            WHERE 1=1
        """
        params = []
        if facility_type:
            query += " AND f.FacilityType = %s"
            params.append(facility_type)
        if status:
            query += " AND f.Status = %s"
            params.append(status)

        query += " ORDER BY f.FacilityID ASC;"
        cur.execute(query, tuple(params))
        return cur.fetchall()


@router.get("/available")
def list_available_facilities(
    booking_date: date = Query(...),
    start_time: time = Query(...),
    end_time: time = Query(...),
    facility_type: Optional[str] = None,
):
    """
    Returns facilities that are currently free and available for booking
    at the specified date and time window.
    """
    with get_db_cursor(commit=False) as cur:
        query = """
            SELECT f.FacilityID, f.Name, f.Location, f.FacilityType, f.Status
            FROM Facility f
            WHERE f.Status = 'Active'
              AND NOT has_maintenance_conflict(f.FacilityID, %s, %s, %s)
              AND check_classroom_availability(f.FacilityID, %s, %s, %s)
              AND NOT EXISTS (
                  SELECT 1 FROM Booking b
                  WHERE b.FacilityID = f.FacilityID
                    AND b.BookingDate = %s
                    AND b.Status = 'Confirmed'
                    AND b.StartTime < %s AND b.EndTime > %s
              )
        """
        params = [
            booking_date, start_time, end_time,
            booking_date, start_time, end_time,
            booking_date, end_time, start_time,
        ]
        if facility_type:
            query += " AND f.FacilityType = %s"
            params.append(facility_type)

        query += " ORDER BY f.FacilityID ASC;"
        cur.execute(query, tuple(params))
        return cur.fetchall()

