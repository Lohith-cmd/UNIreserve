# UNIreserve: Campus Facility Booking System

**CS F212 Database Systems course project, Group 8, BITS Pilani Hyderabad Campus**

Final submission commit: `<FINAL_COMMIT_HASH>` (git tag `final`)

## Description

Students and faculty request bookings for sports venues, classrooms and other campus venues
(Auditorium, Open Amphitheatre). A designated admin approves or rejects each request, and only
confirmed bookings are valid. Booking rules are enforced inside the database with triggers,
constraints and stored functions, so they hold no matter which client calls the API. Confirming one
request automatically rejects every overlapping pending request, which removes scheduling
conflicts without user-side waitlists.

## Team

| # | Name | Student ID |
|---|---|---|
| 1 | Lohith Reddy Thumburu | 2024AAPS0226H |
| 2 | Aditya Maheshwari | 2024AAPS0261H |
| 3 | Sambhav Jain | 2024AAPS0274H |
| 4 | Gowtham Sai Muppidi | 2024AAPS0207H |
| 5 | Aniya Pramod Mulay | 2024AAPS2027H |

### Individual contributions

| Member | Contribution |
|---|---|
| Lohith Reddy Thumburu | Relational schema and integrity constraints; `OtherFacility` subtype and BIGINT user IDs; seed-data generator and full seed; facilities/bookings/admin API routers and test suite |
| Aditya Maheshwari | Assumptions and normalization; triggers, stored functions, indexes and SQL test script; Docker setup; security fix (auth bypass); friendly API errors; maintenance-cancels-bookings trigger; campus-time (IST) fix and first-come ordering |
| Sambhav Jain | ER/EER diagram and relational schema |
| Gowtham Sai Muppidi | Application design and tech stack; RS256 JWT authentication, registration and role dependencies; bookings and admin approval routes; backend Docker image |
| Aniya Pramod Mulay | Application design; React frontend (booking, my bookings, admin approvals, analytics, manage pages) |

## Technology stack

| Layer | Technology |
|---|---|
| Database | PostgreSQL 16 (PL/pgSQL triggers and functions, views, indexes) |
| Backend | FastAPI (Python 3.12), psycopg2 with raw SQL, Pydantic |
| Auth | JWT, RS256, role checked server-side on every protected route |
| Frontend | React 18, Vite, TypeScript, axios |
| Tooling | Docker Compose (db + api), pytest |

## Repository layout

```
db/schema.sql        12 tables, constraints, indexes, 2 views
db/procedures.sql    has_maintenance_conflict, check_classroom_availability, cancel_booking
db/triggers.sql      6 trigger functions (see "Triggers")
db/seed.sql          sample data (about 8,800 rows: 4,160 users, 172 facilities, bookings, logs)
db/tests.sql         SQL test script (every trigger, function and constraint; rolls back)
backend/             FastAPI app (app/) and pytest suite (tests/)
frontend/            React app
docker-compose.yml   Postgres + API
generate_seed_and_tests.py   generator for db/seed.sql (needs the private student workbook, not required to run the app)
```

## Setup and run

Requirements: Docker Desktop, Node 20+ (for the frontend), Python 3.12 (only to run the tests on the host).

### 1. Database and API

```bash
cp .env.example .env
docker compose up -d --build
```

The first start loads `schema.sql`, `procedures.sql`, `triggers.sql` and `seed.sql` automatically.
These scripts only run on an empty volume. After changing any SQL file or the seed, rebuild from scratch:

```bash
docker compose down -v
docker compose up -d --build
```

API docs: http://localhost:8000/docs. Health check: http://localhost:8000/health.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env      # then set VITE_USE_MOCK=false and VITE_API_URL=http://localhost:8000
npm run dev
```

Open http://localhost:5173.

### 3. Demo logins

Every seeded user's password is `Bits@` followed by their UserID.

| Role | Email | Password |
|---|---|---|
| Admin | admin1@hyderabad.bits-pilani.ac.in | `Bits@1` |
| Faculty | psaxena@hyderabad.bits-pilani.ac.in | `Bits@2` |
| Student | f20212331@hyderabad.bits-pilani.ac.in | `Bits@41120212331` |

Facility IDs: classrooms 1001-1156, sports venues 2001-2014, Auditorium and Open Amphitheatre 3001-3002.

### 4. Tests

SQL tests (PowerShell; run on a freshly seeded database, everything is rolled back):

```powershell
Get-Content db/tests.sql -Raw | docker compose exec -T db psql -U unireserve -d unireserve
```

Backend tests (needs the stack above running):

```bash
pip install -r backend/requirements.txt
python -m pytest
```

Note: two cancellation checks (2-hour rule) only run between 05:00 and 20:00 campus time.

## Workflows

1. **Browse and book.** The user picks a date, time and facility type; the API lists facilities that are free
   (correlated `NOT EXISTS` subquery, classroom availability function, maintenance check) and shows how many
   pending requests each already has. Submitting inserts a Pending booking that the triggers validate.
2. **Admin approval.** The admin sees the pending queue (oldest request first within a slot) and confirms or
   rejects. Confirming runs in one transaction and the auto-reject trigger rejects overlapping pending requests.
3. **Analytics.** Admin dashboard built from GROUP BY queries, CTEs and the two views.
4. **My bookings and cancel.** Upcoming and past bookings with the full status timeline from `BookingStatusLog`;
   cancelling calls `cancel_booking`, which enforces the 2-hour rule.
5. **Admin manage.** Add or remove holidays and maintenance windows. A new maintenance window cancels
   affected bookings automatically.

## Business rules (enforced in the database)

- Slots are on 30-minute marks, minimum 30 minutes, end after start.
- Students: at most 1 hour on any facility. Faculty: 1 hour on sports venues, 3 hours on classrooms and other venues.
- Sports venues are open 06:00-22:00; Other venues (Auditorium, Amphitheatre) 08:00-22:00.
- Classrooms are bookable on weekdays only from 18:00, and 08:00-22:00 on weekends and declared holidays.
- Students may book up to 7 days ahead, faculty up to 14; slots in the past or already started are rejected.
- A facility `Under Maintenance`, or inside a maintenance window, cannot be booked.
- Admin approval is required; the system never auto-confirms.
- Confirming is blocked if the user or the facility already has an overlapping Confirmed booking.
- Cancellation is allowed only for the booking owner, at least 2 hours before the start.
- All times are campus time (Asia/Kolkata); the database runs with `timezone=Asia/Kolkata`.

## Triggers

| Trigger | Fires | Purpose |
|---|---|---|
| `trg_booking_duration` | BEFORE INSERT on Booking | Duration limits per role and facility type |
| `trg_booking_classroom_availability` | BEFORE INSERT on Booking | Maintenance, classroom window, sports and other-venue hours |
| `trg_booking_advance_window` | BEFORE INSERT on Booking | 7 / 14 day advance window, no past slots |
| `trg_booking_auto_reject` | AFTER UPDATE of Status on Booking | On Confirm: block if user/facility already confirmed; reject overlapping Pending |
| `trg_booking_audit_log` | AFTER INSERT / UPDATE of Status on Booking | Writes `BookingStatusLog` (actor from `app.current_user_id`) |
| `trg_maintenance_cancel_bookings`, `trg_facility_maintenance_cancel` | AFTER INSERT/UPDATE on MaintenanceSchedule; AFTER UPDATE of Status on Facility | New maintenance cancels Confirmed and rejects Pending bookings in the window (rows kept and logged) |

## Design decisions

- Superclass table is `Users` because `User` is reserved in PostgreSQL. `Users` and `Facility` each have IS-A
  subtype tables sharing the primary key (horizontal split): `Student`, `Faculty`, `Admin`; `SportsVenue`,
  `Classroom`, `OtherFacility`.
- Auto-reject uses time overlap, which is stricter than the exact-slot match proposed in the midsem report.
- The audit-log actor is passed to the database per transaction with `set_config('app.current_user_id', ..., true)`.
- Database errors are turned into clean 4xx messages; constraint failures never echo the failing row.
- Differences from the midsem report: function is `check_classroom_availability`, user table is `Users`,
  `OtherFacility` was added (12 tables), user IDs are BIGINT, `Student.Year` is the admission batch (2020-2024),
  raw psycopg2 is used instead of SQLAlchemy.

## Git workflow

- `main` is always runnable. Changes go in through pull requests from one branch per task.
- Do not commit `.env` or `backend/keys`.
