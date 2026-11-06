# UNIreserve: Campus Facility Booking System

DBMS course project (Group 8), BITS Pilani Hyderabad. Students and faculty request bookings for sports
venues and classrooms; an admin approves or rejects. Triggers, stored functions, views, indexes and
transactions are the core of the design.

Stack: PostgreSQL 16, FastAPI (Python 3.12), React 18 + Vite + TypeScript, Docker Compose.

## Layout

```
db/schema.sql       tables, constraints, indexes, views
db/procedures.sql   check_classroom_availability, has_maintenance_conflict, cancel_booking
db/triggers.sql     5 triggers (see below)
db/seed.sql         sample data
backend/            FastAPI app (not started)
frontend/           React app (not started)
docker-compose.yml  Postgres (api/web services commented until they exist)
```

## Run the database

```bash
cp .env.example .env
docker compose up -d db
docker compose exec db psql -U unireserve -d unireserve
```

Init scripts only run on an empty volume. To rebuild after editing SQL: `docker compose down -v && docker compose up -d db`.

## Design decisions (settled in team discussion)

- Superclass table is `Users`, because `User` is a reserved word in PostgreSQL.
- Function is named `check_classroom_availability` (not `is_classroom_available`).
- Students: max 1 hour per booking for any facility. Faculty: 1 hour sports, 3 hours classrooms.
- Facility status values: `Active`, `Under Maintenance`.
- Triggers:
  1. `trg_booking_duration` (BEFORE INSERT): duration limits
  2. `trg_booking_classroom_availability` (BEFORE INSERT): maintenance, classroom window, sports hours
  3. `trg_booking_advance_window` (BEFORE INSERT): students 7 days ahead, faculty 14, no past slots
  4. `trg_booking_auto_reject` (AFTER UPDATE): on Confirm, rejects overlapping Pending bookings and
     blocks the confirm if the user (or facility) already has an overlapping Confirmed booking
  5. `trg_booking_audit_log` (AFTER INSERT/UPDATE): writes BookingStatusLog
- Auto-reject uses time overlap (stricter than the exact-slot match in the midsem report).
- Audit log actor comes from `set_config('app.current_user_id', ...)`, set by the backend per transaction.

## Work split and order

| Task | Owner | Depends on |
|---|---|---|
| `schema.sql` review/extend, constraints | Lohith, Sambhav | none |
| `procedures.sql`, `triggers.sql`, SQL tests | Aditya | schema |
| `seed.sql` (>= 500 rows) | Sambhav | schema, triggers |
| Backend: auth, facilities, bookings, admin | Gowtham | schema |
| Frontend + docker-compose integration | Aniya | API contract |

## Git workflow

- `main` is always runnable. Never push to it directly.
- One branch per task (`db/triggers`, `backend/auth`, `frontend/booking-form`), merge by pull request with one reviewer.
- Pull before starting work; keep PRs small; do not commit `.env`.

## Status

SQL files are first drafts and have not been executed against Postgres yet. First job for the DB owners:
run them via Docker, fix errors, and add tests that exercise every trigger and CHECK.
