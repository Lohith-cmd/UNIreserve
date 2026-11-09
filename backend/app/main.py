from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import psycopg2
from psycopg2 import errors

from app.database import close_db_pool, get_db_pool
from app.routers import bookings, admin, auth, facilities


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up connection pool on startup
    try:
        get_db_pool()
    except Exception as e:
        print(f"Warning: could not connect to PostgreSQL on startup: {e}")
    yield
    # Clean shutdown
    close_db_pool()


app = FastAPI(
    title="UNIreserve API",
    description="Campus Facility Booking System API (FastAPI + PostgreSQL)",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler for PostgreSQL Trigger & Procedure Errors
@app.exception_handler(psycopg2.Error)
async def postgres_exception_handler(request: Request, exc: psycopg2.Error):
    """
    Catches PostgreSQL RAISE EXCEPTION from triggers and procedures,
    returning clean, user-readable 4xx responses.
    """
    # Triggers and stored procedures raise RaiseException (SQLSTATE P0001)
    if isinstance(exc, errors.RaiseException):
        message = exc.diag.message_primary if exc.diag else str(exc)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": message},
        )
    
    # Unique violation (e.g. duplicate holiday date or user email)
    if isinstance(exc, errors.UniqueViolation):
        message = exc.diag.message_detail or exc.diag.message_primary or "A record with this value already exists."
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": message},
        )

    # Check constraint violation
    if isinstance(exc, errors.CheckViolation):
        message = exc.diag.message_primary or "Input violated a database check constraint."
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": message},
        )

    # Generic database error
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database error occurred", "error": str(exc)},
    )


# Include all routers
app.include_router(auth.router)
app.include_router(facilities.router)
app.include_router(bookings.router)
app.include_router(admin.router)


@app.get("/", tags=["Health"])
def root():
    return {"message": "UNIreserve API is running", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}

