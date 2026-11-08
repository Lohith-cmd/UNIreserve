import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from app.main import app

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
        "facility_id": 1,
        "booking_date": str(target_date),
        "start_time": "10:00:00",
        "end_time": "11:30:00",
        "purpose": "Long match",
    }
    response = client.post("/bookings", json=payload, headers={"X-User-ID": "4"})
    assert response.status_code == 400
    assert "Students may book at most 1 hour per booking" in response.json()["detail"]


def test_create_and_fetch_my_booking():
    """
    Test creating a valid 1-hour student booking and fetching it in /bookings/my.
    """
    target_date = date.today() + timedelta(days=4)
    payload = {
        "facility_id": 1,  # Sports venue
        "booking_date": str(target_date),
        "start_time": "14:00:00",
        "end_time": "15:00:00",
        "purpose": "Basketball practice",
    }
    response = client.post("/bookings", json=payload, headers={"X-User-ID": "4"})
    assert response.status_code == 201
    created = response.json()
    assert created["status"] == "Pending"
    booking_id = created["booking_id"]

    # Verify in my bookings
    my_resp = client.get("/bookings/my", headers={"X-User-ID": "4"})
    assert my_resp.status_code == 200
    my_bookings = my_resp.json()
    assert any(b["booking_id"] == booking_id for b in my_bookings)


def test_admin_confirm_and_reject_flow():
    """
    Test admin confirming a booking and rejecting another.
    """
    target_date = date.today() + timedelta(days=5)

    # User 4 books slot 16:00-17:00
    b1_resp = client.post(
        "/bookings",
        json={
            "facility_id": 2,
            "booking_date": str(target_date),
            "start_time": "16:00:00",
            "end_time": "17:00:00",
            "purpose": "Match A",
        },
        headers={"X-User-ID": "4"},
    )
    assert b1_resp.status_code == 201
    b1_id = b1_resp.json()["booking_id"]

    # User 5 books overlapping slot 16:30-17:30
    b2_resp = client.post(
        "/bookings",
        json={
            "facility_id": 2,
            "booking_date": str(target_date),
            "start_time": "16:30:00",
            "end_time": "17:30:00",
            "purpose": "Match B",
        },
        headers={"X-User-ID": "5"},
    )
    assert b2_resp.status_code == 201
    b2_id = b2_resp.json()["booking_id"]

    # Admin confirms booking 1
    confirm_resp = client.put(f"/admin/bookings/{b1_id}/confirm", headers={"X-User-ID": "1"})
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["status"] == "Confirmed"

    # Auto-reject trigger (trg_booking_auto_reject) must have marked booking 2 as Rejected!
    b2_check = client.get("/bookings/my", headers={"X-User-ID": "5"})
    b2_data = next(b for b in b2_check.json() if b["booking_id"] == b2_id)
    assert b2_data["status"] == "Rejected"


def test_admin_analytics():
    response = client.get("/admin/analytics", headers={"X-User-ID": "1"})
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "status_counts" in data
    assert "top_facilities" in data


def test_holidays_crud():
    holiday_date = str(date.today() + timedelta(days=20))
    # Create
    create_resp = client.post(
        "/admin/holidays",
        json={"holiday_date": holiday_date, "description": "Test Campus Holiday"},
        headers={"X-User-ID": "1"},
    )
    assert create_resp.status_code == 201
    h_id = create_resp.json()["holiday_id"]

    # List
    list_resp = client.get("/admin/holidays", headers={"X-User-ID": "1"})
    assert any(h["holiday_id"] == h_id for h in list_resp.json())

    # Delete
    del_resp = client.delete(f"/admin/holidays/{h_id}", headers={"X-User-ID": "1"})
    assert del_resp.status_code == 204


def test_maintenance_crud():
    start_d = str(date.today() + timedelta(days=25))
    end_d = str(date.today() + timedelta(days=26))
    create_resp = client.post(
        "/admin/maintenance",
        json={
            "facility_id": 1,
            "start_date": start_d,
            "end_date": end_d,
            "start_time": "08:00:00",
            "end_time": "12:00:00",
            "description": "Floor resurfacing",
        },
        headers={"X-User-ID": "1"},
    )
    assert create_resp.status_code == 201
    m_id = create_resp.json()["schedule_id"]

    # Delete
    del_resp = client.delete(f"/admin/maintenance/{m_id}", headers={"X-User-ID": "1"})
    assert del_resp.status_code == 204
