# backend

FastAPI (Python 3.12) service for UNIreserve. See the root README for setup and run instructions.

Routers: `/auth` (login, register, me), `/facilities` (list, available), `/bookings` (create, my, logs, cancel),
`/admin` (pending queue, confirm, reject, analytics, holidays, maintenance).

Rules for DB access:
- Raw SQL via psycopg2 for conflict checks and analytics CTEs.
- Inside every transaction that changes a booking, `get_db_cursor(commit=True, user_id=...)` runs
  `SELECT set_config('app.current_user_id', '<user id>', true);` so the audit trigger records who acted.
- DB errors raised by triggers/functions (`RAISE EXCEPTION`) become 400 responses with the trigger message;
  constraint violations map to friendly messages and never expose the failing row.
- Authentication is a Bearer RS256 JWT only; admin routes re-read the role from the database.
- Timestamps are returned tagged `+05:30` (campus time) so browsers display them correctly.

Run the tests from the repository root with the stack running: `python -m pytest`.
