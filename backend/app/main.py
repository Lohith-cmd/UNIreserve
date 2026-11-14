"""
backend/app/main.py
====================
FastAPI application entry-point for UNIreserve.

Startup:
  - Warms up the PostgreSQL connection pool.
  - Generates RSA 2048-bit keypair (if not already on disk) for RS256 JWT signing.

Middleware:
  - CORSMiddleware: open during development (configure origins in production).

Exception handlers:
  - psycopg2.errors.RaiseException (SQLSTATE P0001) → HTTP 400 with trigger message.
  - psycopg2.errors.UniqueViolation                 → HTTP 409, friendly message.
  - psycopg2.errors.CheckViolation                  → HTTP 400, friendly message.
  - Any other psycopg2.Error                        → HTTP 500, generic message (details logged).
  Constraint errors never include the failing row or key value.
"""

import logging
from contextlib import asynccontextmanager

import psycopg2
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from psycopg2 import errors

from app.auth_utils import get_jwt_keys
from app.database import close_db_pool, get_db_pool
from app.routers import admin, auth, bookings, facilities


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────────
    # 1. Pre-generate RSA keypair so the keys/ directory and .gitignore exist.
    try:
        get_jwt_keys()
    except Exception as e:
        print(f"Warning: could not initialise JWT keys on startup: {e}")

    # 2. Warm up PostgreSQL connection pool.
    try:
        get_db_pool()
    except Exception as e:
        print(f"Warning: could not connect to PostgreSQL on startup: {e}")

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────────
    close_db_pool()


app = FastAPI(
    title="UNIreserve API",
    description="Campus Facility Booking System — FastAPI + PostgreSQL 16 + RS256 JWT",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # restrict to frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Global PostgreSQL exception handlers
# ---------------------------------------------------------------------------

logger = logging.getLogger("unireserve")

# Friendly messages keyed by constraint name (see db/schema.sql).
CHECK_MESSAGES = {
    "chk_booking_slot_grid": "Booking times must be on 30-minute marks, for example 10:00 or 10:30.",
    "chk_booking_time_order": "End time must be after the start time.",
    "chk_maint_dates": "The end date must be on or after the start date.",
    "classroom_capacity_check": "Capacity must be greater than zero.",
    "otherfacility_capacity_check": "Capacity must be greater than zero.",
    "student_year_check": "Year is outside the allowed range.",
}
UNIQUE_MESSAGES = {
    "users_email_key": "Email already registered",
    "student_bits_id_key": "BITS ID already registered",
    "faculty_employeeid_key": "Employee ID already registered",
    "holiday_holidaydate_key": "A holiday already exists on that date.",
}


@app.exception_handler(psycopg2.Error)
async def postgres_exception_handler(request: Request, exc: psycopg2.Error):
    """
    Converts psycopg2 database errors into clean HTTP responses so the React
    frontend never receives a raw traceback.

    SQLSTATE P0001 (RAISE EXCEPTION from triggers/procedures) → 400
    SQLSTATE 23505 (UniqueViolation)                          → 409
    SQLSTATE 23514 (CheckViolation)                           → 400
    Everything else                                           → 500
    """
    if isinstance(exc, errors.RaiseException):
        message = (exc.diag.message_primary if exc.diag else None) or str(exc)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": message},
        )

    # Constraint violations: never echo Postgres's message_detail, which contains the
    # failing row ("Failing row contains (...)") or the offending key value.
    constraint = (exc.diag.constraint_name if exc.diag else None) or ""

    if isinstance(exc, errors.UniqueViolation):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": UNIQUE_MESSAGES.get(constraint, "A record with this value already exists.")},
        )

    if isinstance(exc, errors.CheckViolation):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": CHECK_MESSAGES.get(constraint, "The submitted values are not allowed.")},
        )

    if isinstance(exc, errors.ForeignKeyViolation):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "This item refers to something that does not exist, or is still in use by other records."},
        )

    if isinstance(exc, errors.NotNullViolation):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "A required field is missing."},
        )

    # Catch-all: log the details server-side, return nothing internal to the client.
    logger.exception("Unhandled database error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database error occurred"},
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(facilities.router)
app.include_router(bookings.router)
app.include_router(admin.router)


# ---------------------------------------------------------------------------
# Health endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"])
def root():
    return {"message": "UNIreserve API is running", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
