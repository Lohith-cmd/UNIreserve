import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from app.main import app
from tests.helpers import auth

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_facilities():
    response = client.get("/facilities")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 5


def test_booking_student_duration_exceeded():
    """
    Students are restricted to 1 hour max by trg_booking_duration.
    Booking 1.5 hours should return a 400 with readable trigger message.
    """
    target_date = date.today() + timedelta(days=3)
    payload = {
        "facility_id": 2001,
        "booking_date": str(target_date),
        "start_time": "10:00:00",
        "end_time": "11:30:00",
        "purpose": "Long match",
    }
    response = client.post("/bookings", json=payload, headers=auth(41120212331))
    assert response.status_code == 400
    assert "Students may book at most 1 hour per booking" in response.json()["detail"]


def test_create_and_fetch_my_booking():
    """
    Test creating a valid 1-hour student booking and fetching it in /bookings/my.
    """
    target_date = date.today() + timedelta(days=4)
    payload = {
        "facility_id": 2001,  # Sports venue
        "booking_date": str(target_date),
        "start_time": "14:00:00",
        "end_time": "15:00:00",
        "purpose": "Basketball practice",
    }
    response = client.post("/bookings", json=payload, headers=auth(41120212331))
    assert response.status_code == 201
    created = response.json()
    assert created["status"] == "Pending"
    booking_id = created["booking_id"]

    try:
        # Verify in my bookings
        my_resp = client.get("/bookings/my", headers=auth(41120212331))
        assert my_resp.status_code == 200
        my_bookings = my_resp.json()
        assert any(b["booking_id"] == booking_id for b in my_bookings)
    finally:
        from app.database import get_db_cursor
        with get_db_cursor(commit=True) as cur:
            cur.execute("DELETE FROM BookingStatusLog WHERE BookingID = %s;", (booking_id,))
            cur.execute("DELETE FROM Booking WHERE BookingID = %s;", (booking_id,))


def test_admin_confirm_and_reject_flow():
    """
    Test admin confirming a booking and rejecting another.
    """
    target_date = date.today() + timedelta(days=5)

    # Student 41120212331 books slot 16:00-17:00
    b1_resp = client.post(
        "/bookings",
        json={
            "facility_id": 2002,
            "booking_date": str(target_date),
            "start_time": "16:00:00",
            "end_time": "17:00:00",
            "purpose": "Match A",
        },
        headers=auth(41120212331),
    )
    assert b1_resp.status_code == 201
    b1_id = b1_resp.json()["booking_id"]

    # Student 41120212371 books overlapping slot 16:30-17:30
    b2_resp = client.post(
        "/bookings",
        json={
            "facility_id": 2002,
            "booking_date": str(target_date),
            "start_time": "16:30:00",
            "end_time": "17:30:00",
            "purpose": "Match B",
        },
        headers=auth(41120212371),
    )
    assert b2_resp.status_code == 201
    b2_id = b2_resp.json()["booking_id"]

    try:
        # Admin confirms booking 1
        confirm_resp = client.put(f"/admin/bookings/{b1_id}/confirm", headers=auth(1))
        assert confirm_resp.status_code == 200
        assert confirm_resp.json()["status"] == "Confirmed"

        # Auto-reject trigger (trg_booking_auto_reject) must have marked booking 2 as Rejected!
        b2_check = client.get("/bookings/my", headers=auth(41120212371))
        b2_data = next(b for b in b2_check.json() if b["booking_id"] == b2_id)
        assert b2_data["status"] == "Rejected"
    finally:
        from app.database import get_db_cursor
        with get_db_cursor(commit=True) as cur:
            cur.execute("DELETE FROM BookingStatusLog WHERE BookingID IN (%s, %s);", (b1_id, b2_id))
            cur.execute("DELETE FROM Booking WHERE BookingID IN (%s, %s);", (b1_id, b2_id))


def test_admin_analytics():
    response = client.get("/admin/analytics", headers=auth(1))
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "weekly_summary" in data
    assert "status_counts" in data
    assert "status_breakdown" in data
    assert "role_breakdown" in data
    assert "top_facilities" in data
    assert "peak_hours" in data
    assert "upcoming_availability" in data
    assert len(data["upcoming_availability"]) >= 1


def test_holidays_crud():
    holiday_date = str(date.today() + timedelta(days=20))
    # Create
    create_resp = client.post(
        "/admin/holidays",
        json={"holiday_date": holiday_date, "description": "Test Campus Holiday"},
        headers=auth(1),
    )
    assert create_resp.status_code == 201
    h_id = create_resp.json()["holiday_id"]

    # List
    list_resp = client.get("/admin/holidays", headers=auth(1))
    assert any(h["holiday_id"] == h_id for h in list_resp.json())

    # Delete
    del_resp = client.delete(f"/admin/holidays/{h_id}", headers=auth(1))
    assert del_resp.status_code == 204


def test_maintenance_crud():
    start_d = str(date.today() + timedelta(days=25))
    end_d = str(date.today() + timedelta(days=26))
    create_resp = client.post(
        "/admin/maintenance",
        json={
            "facility_id": 2001,
            "start_date": start_d,
            "end_date": end_d,
            "start_time": "08:00:00",
            "end_time": "12:00:00",
            "description": "Floor resurfacing",
        },
        headers=auth(1),
    )
    assert create_resp.status_code == 201
    m_id = create_resp.json()["schedule_id"]

    # Delete
    del_resp = client.delete(f"/admin/maintenance/{m_id}", headers=auth(1))
    assert del_resp.status_code == 204


def test_cancel_booking_success_and_ownership():
    """
    1. Student 41120212331 creates a booking > 2 hours in the future.
    2. Another student (41120212371) tries to cancel it -> HTTP 400 ('does not belong to user').
    3. Owner (41120212331) cancels via PUT /bookings/{id}/cancel -> Status == 'Cancelled'.
    4. BookingStatusLog contains the 'Cancelled' entry with ChangedByUserID == 41120212331.
    """
    target_date = date.today() + timedelta(days=4)
    create_resp = client.post(
        "/bookings",
        json={
            "facility_id": 2001,
            "booking_date": str(target_date),
            "start_time": "10:00:00",
            "end_time": "11:00:00",
            "purpose": "Cancel ownership test",
        },
        headers=auth(41120212331),
    )
    assert create_resp.status_code == 201
    booking_id = create_resp.json()["booking_id"]

    try:
        # Wrong user attempts cancellation -> 400
        wrong_resp = client.put(
            f"/bookings/{booking_id}/cancel",
            headers=auth(41120212371),
        )
        assert wrong_resp.status_code == 400
        assert "does not belong to user" in wrong_resp.json()["detail"]

        # Owner cancels -> 200 & Status == 'Cancelled'
        cancel_resp = client.put(
            f"/bookings/{booking_id}/cancel",
            headers=auth(41120212331),
        )
        assert cancel_resp.status_code == 200
        cancel_data = cancel_resp.json()
        assert cancel_data["booking_id"] == booking_id
        assert cancel_data["status"] == "Cancelled"

        # Verify BookingStatusLog via /bookings/{id}/logs and /bookings/my
        logs_resp = client.get(
            f"/bookings/{booking_id}/logs",
            headers=auth(41120212331),
        )
        assert logs_resp.status_code == 200
        logs = logs_resp.json()
        assert any(
            entry["new_status"] == "Cancelled" and entry["changed_by_user_id"] == 41120212331
            for entry in logs
        )

        my_resp = client.get("/bookings/my", headers=auth(41120212331))
        assert my_resp.status_code == 200
        my_booking = next(b for b in my_resp.json() if b["booking_id"] == booking_id)
        assert my_booking["status"] == "Cancelled"
        assert my_booking["facility_location"] is not None
        assert any(
            entry["new_status"] == "Cancelled" and entry["changed_by_user_id"] == 41120212331
            for entry in my_booking["status_logs"]
        )
    finally:
        from app.database import get_db_cursor
        with get_db_cursor(commit=True) as cur:
            cur.execute("DELETE FROM BookingStatusLog WHERE BookingID = %s;", (booking_id,))
            cur.execute("DELETE FROM Booking WHERE BookingID = %s;", (booking_id,))


def test_auto_reject_overlapping_pending_bookings():
    """
    Two students submit overlapping pending bookings for facility 2001 (10:00-11:00 and 10:30-11:30).
    Admin (1) confirms the first booking -> trg_booking_auto_reject automatically sets the
    second booking to 'Rejected' and logs both changes with ChangedByUserID == 1.
    """
    target_date = date.today() + timedelta(days=5)

    b1_resp = client.post(
        "/bookings",
        json={
            "facility_id": 2001,
            "booking_date": str(target_date),
            "start_time": "10:00:00",
            "end_time": "11:00:00",
            "purpose": "Overlap slot 1",
        },
        headers=auth(41120212331),
    )
    assert b1_resp.status_code == 201
    b1_id = b1_resp.json()["booking_id"]

    b2_resp = client.post(
        "/bookings",
        json={
            "facility_id": 2001,
            "booking_date": str(target_date),
            "start_time": "10:30:00",
            "end_time": "11:30:00",
            "purpose": "Overlap slot 2",
        },
        headers=auth(41120212371),
    )
    assert b2_resp.status_code == 201
    b2_id = b2_resp.json()["booking_id"]

    try:
        # Confirm both appear in admin pending queue
        pending_resp = client.get("/admin/bookings/pending", headers=auth(1))
        assert pending_resp.status_code == 200
        pending_ids = {item["booking_id"] for item in pending_resp.json()}
        assert b1_id in pending_ids and b2_id in pending_ids

        # Admin confirms booking 1
        confirm_resp = client.put(
            f"/admin/bookings/{b1_id}/confirm",
            headers=auth(1),
        )
        assert confirm_resp.status_code == 200
        assert confirm_resp.json()["status"] == "Confirmed"

        # Verify booking 2 was auto-rejected
        b2_my = client.get("/bookings/my", headers=auth(41120212371))
        assert b2_my.status_code == 200
        b2_data = next(b for b in b2_my.json() if b["booking_id"] == b2_id)
        assert b2_data["status"] == "Rejected"

        # Verify BookingStatusLog recorded ChangedByUserID == 1 for the auto-rejection
        assert any(
            entry["old_status"] == "Pending"
            and entry["new_status"] == "Rejected"
            and entry["changed_by_user_id"] == 1
            for entry in b2_data["status_logs"]
        )
    finally:
        from app.database import get_db_cursor
        with get_db_cursor(commit=True) as cur:
            cur.execute("DELETE FROM BookingStatusLog WHERE BookingID IN (%s, %s);", (b1_id, b2_id))
            cur.execute("DELETE FROM Booking WHERE BookingID IN (%s, %s);", (b1_id, b2_id))


def test_available_facilities_endpoint():
    """
    Calls GET /facilities/available for a future date (18:00-19:00) and verifies:
    - Active facilities (e.g. 2001, 1001) are returned.
    - Facilities with Status = 'Under Maintenance' (2003) and facilities with a
      MaintenanceSchedule conflict (2002) are excluded.
    """
    from app.database import get_db_cursor

    target_date = date.today() + timedelta(days=6)
    maint_id = None

    with get_db_cursor(commit=True) as cur:
        cur.execute("UPDATE Facility SET Status = 'Under Maintenance' WHERE FacilityID = 2003;")

    try:
        # Create a MaintenanceSchedule conflict on 2002 for 17:00-20:00
        m_resp = client.post(
            "/admin/maintenance",
            json={
                "facility_id": 2002,
                "start_date": str(target_date),
                "end_date": str(target_date),
                "start_time": "17:00:00",
                "end_time": "20:00:00",
                "description": "Availability exclusion test",
            },
            headers=auth(1),
        )
        assert m_resp.status_code == 201
        maint_id = m_resp.json()["schedule_id"]

        avail_resp = client.get(
            "/facilities/available",
            params={
                "date": str(target_date),
                "start_time": "18:00:00",
                "end_time": "19:00:00",
            },
        )
        assert avail_resp.status_code == 200
        avail_ids = {f["facility_id"] for f in avail_resp.json()}

        assert 2001 in avail_ids
        assert 1001 in avail_ids
        assert 2003 not in avail_ids  # Status = 'Under Maintenance'
        assert 2002 not in avail_ids  # Overlaps MaintenanceSchedule
    finally:
        if maint_id is not None:
            client.delete(f"/admin/maintenance/{maint_id}", headers=auth(1))
        with get_db_cursor(commit=True) as cur:
            cur.execute("UPDATE Facility SET Status = 'Active' WHERE FacilityID = 2003;")
