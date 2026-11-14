import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_auth_status():
    response = client.get("/auth/status")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["algorithm"] == "RS256"


def test_login_success_student():
    """
    Test student login using seeded credentials (plain seed password fallback).
    """
    payload = {
        "email": "f20212331@hyderabad.bits-pilani.ac.in",
        "password": "Bits@41120212331",
    }
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "f20212331@hyderabad.bits-pilani.ac.in"
    assert data["user"]["role"] == "Student"
    assert data["user"]["bits_id"] is not None


def test_login_success_admin():
    """
    Test admin login using seeded credentials.
    """
    payload = {
        "email": "admin1@hyderabad.bits-pilani.ac.in",
        "password": "Bits@1",
    }
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["role"] == "Admin"
    assert data["user"]["admin_level"] == "Level 3 - Campus"


def test_login_success_faculty():
    """
    Test faculty login using seeded credentials.
    """
    payload = {
        "email": "psaxena@hyderabad.bits-pilani.ac.in",
        "password": "Bits@2",
    }
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["role"] == "Faculty"
    assert data["user"]["employee_id"] is not None


def test_login_invalid_password():
    payload = {
        "email": "admin1@hyderabad.bits-pilani.ac.in",
        "password": "WrongPassword!123",
    }
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_nonexistent_user():
    payload = {
        "email": "doesnotexist999@hyderabad.bits-pilani.ac.in",
        "password": "AnyPassword123",
    }
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 401


def test_auth_me_with_jwt():
    # 1. Login as student
    login_resp = client.post(
        "/auth/login",
        json={
            "email": "f20212331@hyderabad.bits-pilani.ac.in",
            "password": "Bits@41120212331",
        },
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # 2. Call /auth/me with Bearer token
    me_resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    user_data = me_resp.json()
    assert user_data["email"] == "f20212331@hyderabad.bits-pilani.ac.in"
    assert user_data["role"] == "Student"


def test_auth_me_invalid_token():
    response = client.get("/auth/me", headers={"Authorization": "Bearer not.a.valid.jwt.token"})
    assert response.status_code == 401


def test_student_register_and_login():
    """
    Registers a new student, verifies bcrypt hashing, and logs in.
    """
    uid = uuid.uuid4().hex[:6]
    student_payload = {
        "name": f"Test Student {uid}",
        "email": f"student_{uid}@hyderabad.bits-pilani.ac.in",
        "password": "SecurePassword#2026",
        "phone": "9876543210",
        "bits_id": f"2024A7PS{uid[:4].upper()}H",
        "department": "Computer Science",
        "year": 2024,
    }

    reg_resp = client.post("/auth/register/student", json=student_payload)
    assert reg_resp.status_code == 201
    reg_data = reg_resp.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == student_payload["email"]
    assert reg_data["user"]["role"] == "Student"

    # Login with new credentials
    login_resp = client.post(
        "/auth/login",
        json={
            "email": student_payload["email"],
            "password": "SecurePassword#2026",
        },
    )
    assert login_resp.status_code == 200
    assert login_resp.json()["user"]["email"] == student_payload["email"]


def test_admin_route_secured_with_jwt():
    # 1. Admin login
    admin_login = client.post(
        "/auth/login",
        json={
            "email": "admin1@hyderabad.bits-pilani.ac.in",
            "password": "Bits@1",
        },
    )
    admin_token = admin_login.json()["access_token"]

    # 2. Access /admin/analytics with Admin token
    analytics_resp = client.get(
        "/admin/analytics",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert analytics_resp.status_code == 200
    assert "summary" in analytics_resp.json()

    # 3. Student login
    student_login = client.post(
        "/auth/login",
        json={
            "email": "f20212331@hyderabad.bits-pilani.ac.in",
            "password": "Bits@41120212331",
        },
    )
    student_token = student_login.json()["access_token"]

    # 4. Access /admin/analytics with Student token -> 403 Forbidden
    forbidden_resp = client.get(
        "/admin/analytics",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert forbidden_resp.status_code == 403
    assert "Admin privileges required" in forbidden_resp.json()["detail"]


# ---------------------------------------------------------------------------
# Regression tests: the old X-User-ID / default-user bypass must stay closed
# ---------------------------------------------------------------------------
def test_no_credentials_rejected():
    assert client.get("/bookings/my").status_code == 401
    assert client.get("/admin/analytics").status_code == 401
    assert client.get("/auth/me").status_code == 401


def test_x_user_id_header_no_longer_grants_access():
    """Anyone sending X-User-ID: 1 used to be treated as the admin."""
    resp = client.get("/admin/analytics", headers={"X-User-ID": "1"})
    assert resp.status_code == 401
    resp = client.get("/bookings/my", headers={"X-User-ID": "41120212331"})
    assert resp.status_code == 401


def test_garbage_and_tampered_tokens_rejected():
    assert client.get("/bookings/my", headers={"Authorization": "Bearer not.a.token"}).status_code == 401
    assert client.get("/bookings/my", headers={"Authorization": "Basic abc"}).status_code == 401
    from tests.helpers import auth
    good = auth(41120212331)["Authorization"]
    tampered = good[:-4] + ("AAAA" if not good.endswith("AAAA") else "BBBB")
    assert client.get("/bookings/my", headers={"Authorization": tampered}).status_code == 401


def test_expired_token_rejected():
    from datetime import timedelta
    from app.auth_utils import create_access_token
    token = create_access_token({"sub": "41120212331"}, expires_delta=timedelta(minutes=-5))
    resp = client.get("/bookings/my", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
