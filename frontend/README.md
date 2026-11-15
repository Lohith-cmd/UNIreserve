# UNIreserve frontend

React 18 + Vite + TypeScript client for the UNIreserve campus facility booking system. It supports three roles (Student, Faculty, Admin) with role-based routing.

## Quick start

Requires Node 20 or newer.

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open the URL Vite prints (usually http://localhost:5173).

## Environment variables

Set these in `frontend/.env`. This file is git-ignored; `.env.example` is the template. Restart `npm run dev` after changing it.

| Variable | Default | Meaning |
|---|---|---|
| `VITE_USE_MOCK` | `true` | `true` uses the built-in fake API, `false` calls the real backend |
| `VITE_API_URL` | `http://localhost:8000` | Base URL of the FastAPI backend |

## Mock mode (default)

With `VITE_USE_MOCK=true` no backend or database is needed. The app runs on in-memory sample data that resets on page refresh. The mock also enforces the main booking rules, so errors look like the real ones.

On the login page, use the quick-login buttons, or sign in with any password and one of:

| Role | Email |
|---|---|
| Student | student@uni.edu (also student2@uni.edu, student3@uni.edu) |
| Faculty | faculty@uni.edu (also faculty2@uni.edu) |
| Admin | admin@uni.edu |

## Real backend mode

1. Start the database and API from the repo root (see the root README and `TEAM_GUIDE.md`).
2. Set `VITE_USE_MOCK=false` in `frontend/.env`.
3. Restart `npm run dev` and log in with a seeded account (email plus password).

The backend must allow CORS for `http://localhost:5173`.

Status: the API layer is written against the backend's Pydantic schemas, but has not yet been verified end to end against a live backend. Some analytics keys and delete endpoints are assumptions (see Known gaps).

## Pages

| Route | Role | Page |
|---|---|---|
| `/login` | everyone | Sign in |
| `/book` | Student, Faculty | Search availability by date, time and type, then request a booking |
| `/my-bookings` | Student, Faculty | Upcoming and history tabs, status timeline, cancel |
| `/admin` | Admin | Pending approval queue, grouped by facility and date |
| `/admin/analytics` | Admin | Status counts, most-booked facilities, busiest slots, role breakdown, weekly summary |
| `/admin/manage` | Admin | Add and delete holidays and maintenance schedules |

## Project structure

```
src/
  api/          API layer: real axios calls, mock mode, mappers, error handling
  components/   Layout, ProtectedRoute, StatusBadge, BarList
  context/      Auth provider and hook (JWT and user kept in localStorage)
  pages/        One file per route
  types/        Shared TypeScript types
  utils/        Client-side validation, helpers
```

## How the API layer works

Pages only import from `src/api`. Each function there either returns mock data or calls the backend.

- `api/index.ts`: every API function, with its mock and real branch.
- `api/mappers.ts`: converts the