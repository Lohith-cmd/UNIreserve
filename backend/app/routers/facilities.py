"""
backend/app/routers/facilities.py
==================================
Facility listing and availability query router.

GET /facilities        — All facilities with subtype details (LEFT JOINed)
GET /facilities/available — Facilities free for a given date/time window
"""

from datetime import date, time
from typing import List, Optional

from fastapi import APIRouter, Query
from app.database import get_db_cursor

router = APIRouter(prefix="/facilities", tags=["Facilities"])


@router.get("")
def list_facilities(
    facility_type: Optional[str] = None,
    status: Optional[str] = None,
):
    """
    Returns all facilities (Sports 2001+, Classroom 1001+, Other 3001+)
    LEFT JOINed with their subtype tables to include:
      - Classroom: capacity, building, room number, projector/AC flags, room type
      - SportsVenue: venue type, surface, indoor/outdoor
      - OtherFacility: category, capacity, projector/AC flags, indoor/outdoor
    """
    with get_db_cursor(commit=False) as cur:
        query = """
            SELECT
                f.FacilityID   AS facility_id,
                f.Name         AS name,
                f.Location     AS location,
                f.FacilityType AS facility_type,
                f.Status       AS status,
                -- Sports
                s.VenueType    AS venue_type,
                s.Surface      AS surface,
                -- Classroom
                c.BuildingName AS building_name,
                c.RoomNumber   AS room_number,
                c.RoomType     AS room_type,
                -- Other
                o.VenueCategory AS venue_category,
                -- Shared numeric/bool (COALESCE classroom vs other)
                COALESCE(c.Capacity,     o.Capacity)       AS capacity,
                COALESCE(c.HasProjector, o.HasProjector)   AS has_projector,
                COALESCE(c.HasAC,        o.HasAC)          AS has_ac,
                COALESCE(s.IndoorOutdoor, o.IndoorOutdoor) AS indoor_outdoor
            FROM Facility f
            LEFT JOIN SportsVenue s  ON s.FacilityID = f.FacilityID
            LEFT JOIN Classroom   c  ON c.FacilityID = f.FacilityID
            LEFT JOIN OtherFacility o ON o.FacilityID = f.FacilityID
            WHERE 1=1
        """
        params: list = []
        if facility_type:
            query += " AND f.FacilityType = %s"
            params.append(facility_type)
        if status:
            query += " AND f.Status = %s"
            params.append(status)

        query += " ORDER BY f.FacilityID ASC;"
        cur.execute(query, tuple(params))
        return [dict(row) for row in cur.fetchall()]


@router.get("/available")
def list_available_facilities(
    date: Optional[date] = Query(None, description="Booking date"),
    booking_date: Optional[date] = Query(None, description="Booking date (alias)"),
    start_time: time = Query(...),
    end_time: time = Query(...),
    facility_type: Optional[str] = Query(None),
):
    """
    Returns facilities that are free and bookable for the given date/time window.

    Supports both ?date= and ?booking_date= query parameters.
    """
    target_date = date or booking_date
    if not target_date:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="Query parameter 'date' or 'booking_date' is required.")

    with get_db_cursor(commit=False) as cur:
        query = """
            SELECT
                f.FacilityID   AS facility_id,
                f.Name         AS name,
                f.Location     AS location,
                f.FacilityType AS facility_type,
                f.Status       AS status,
                s.VenueType    AS venue_type,
                s.Surface      AS surface,
                c.BuildingName AS building_name,
                c.RoomNumber   AS room_number,
                c.RoomType     AS room_type,
                o.VenueCategory AS venue_category,
                COALESCE(c.Capacity,     o.Capacity)       AS capacity,
                COALESCE(c.HasProjector, o.HasProjector)   AS has_projector,
                COALESCE(c.HasAC,        o.HasAC)          AS has_ac,
                COALESCE(s.IndoorOutdoor, o.IndoorOutdoor) AS indoor_outdoor,
                -- Count overlapping Pending requests as a demand signal
                (
                    SELECT COUNT(*)
                    FROM Booking b2
                    WHERE b2.FacilityID  = f.FacilityID
                      AND b2.BookingDate = %s
                      AND b2.Status      = 'Pending'
                      AND b2.StartTime   < %s
                      AND b2.EndTime     > %s
                ) AS pending_requests
            FROM Facility f
            LEFT JOIN SportsVenue   s ON s.FacilityID = f.FacilityID
            LEFT JOIN Classroom     c ON c.FacilityID = f.FacilityID
            LEFT JOIN OtherFacility o ON o.FacilityID = f.FacilityID
            WHERE
                -- 1+2. Must be Active AND no maintenance window overlap
                f.Status = 'Active'
                AND NOT has_maintenance_conflict(f.FacilityID, %s, %s, %s)

                -- 3. Classroom operating-hours check (returns TRUE for non-classrooms)
                AND check_classroom_availability(f.FacilityID, %s, %s, %s)

                -- 4. Sports venue operating hours: 06:00–22:00
                AND NOT (
                    f.FacilityType = 'Sports'
                    AND (%s < TIME '06:00' OR %s > TIME '22:00')
                )

                -- 5. Other venue operating hours: 08:00–22:00
                AND NOT (
                    f.FacilityType = 'Other'
                    AND (%s < TIME '08:00' OR %s > TIME '22:00')
                )

                -- 6. No confirmed booking overlapping the requested slot
                AND NOT EXISTS (
                    SELECT 1
                    FROM Booking b
                    WHERE b.FacilityID  = f.FacilityID
                      AND b.BookingDate = %s
                      AND b.Status      = 'Confirmed'
                      AND b.StartTime   < %s   -- confirmed starts before our end
                      AND b.EndTime     > %s   -- confirmed ends after our start
                )
        """

        # Parameter order matches placeholders above:
        params: list = [
            # pending_requests subquery
            target_date, end_time, start_time,
            # has_maintenance_conflict
            target_date, start_time, end_time,
            # check_classroom_availability
            target_date, start_time, end_time,
            # sports hours
            start_time, end_time,
            # other hours
            start_time, end_time,
            # no confirmed overlap
            target_date, end_time, start_time,
        ]

        if facility_type:
            query += " AND f.FacilityType = %s"
            params.append(facility_type)

        query += " ORDER BY f.FacilityID ASC;"
        cur.execute(query, tuple(params))
        return [dict(row) for row in cur.fetchall()]
