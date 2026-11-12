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
  - psycopg2.errors.UniqueViolation                 → HTTP 409.
  - psycopg2.errors.CheckViolation                  → HTTP 400.
  - Any other psycopg2.Error                        → HTTP 500.
"""

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

    if isinstance(exc, errors.UniqueViolation):
        message = (
            (exc.diag.message_detail if exc.diag else None)
            or (exc.diag.message_primary if exc.diag else None)
            or "A record with this value already exists."
        )
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": message},
        )

    if isinstance(exc, (errors.CheckViolation, errors.ForeignKeyViolation, errors.NotNullViolation)):
        message = (
            (exc.diag.message_detail if exc.diag else None)
            or (exc.diag.message_primary if exc.diag else None)
            or "Input violated a database constraint."
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": message},
        )

    # Catch-all
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database error occurred", "error": str(exc)},
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
