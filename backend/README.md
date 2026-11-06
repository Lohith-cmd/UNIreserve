# backend

FastAPI (Python 3.12) app. Not started yet.

Planned routers: `/auth`, `/facilities`, `/bookings`, `/admin` (see root README).

Rules for DB access:
- Raw SQL via psycopg2 for conflict checks and analytics CTEs.
- Inside every transaction that changes a booking, run
  `SELECT set_config('app.current_user_id', '<user id>', true);` so the audit trigger records who acted.
- DB errors raised by triggers/functions (RAISE EXCEPTION) should be turned into 4xx responses with the message.
