# Barber Booking System

A backend API that replaces phone-call scheduling in barber shops with fixed booking slots. Each barber has working hours, the system turns those hours into fixed-duration slots, and clients book slots instead of calling at random times.

**Live API docs (Swagger):** `<production-url>/docs`

## Why this exists

A barber shop queue gets messy fast: one client calls, another walks in, a third says "I'll come back in 15 minutes," and the schedule falls apart. This project gives each barber a clear set of slots, and makes sure that **two clients can never end up holding the same slot**, even if they tap "Book" at the same moment. That last part is the centerpiece of the project.

## Tech stack

| Tool | Why |
|---|---|
| **FastAPI** | Validates input and generates API docs automatically, and supports async. I already knew it well. Flask would need extra libraries for both, and Django is heavier than a pure API needs. |
| **PostgreSQL (Neon)** | Row-level locking allows many concurrent writers, and it runs as a separate hosted service. SQLite locks the whole database per write and is stored as a file inside the app. |
| **SQLAlchemy** | ORM for models and queries. |
| **JWT + RBAC** | Stateless authentication with client / barber / owner roles. |
| **APScheduler** | Nightly slot generation. |
| **Railway** | Hosts the API. |
| **GitHub Actions** | CI for the test suite. |

## Key features

- **Slot generation.** When a barber registers with working hours, 14 days of fixed-duration slots are generated immediately. A nightly job then generates the slots for day 14 ahead, so the window stays 14 days long.
- **Booking and cancellation** that are safe under concurrent requests (see below).
- **Roles:** clients book and cancel; barbers manage their own bookings; shop owners manage the shop.
- **Client CRUD.**
- **Barber deactivation** with cascading shop-closure logic.
- **Multi-tenancy audit** documented for the project.

## Concurrency design

### The problem

Two clients tap "Book" on the same 3:00 PM slot at the same moment.

The naive approach is **read, then write**: read the slot, check that it is open, then update it. The gap between the check and the write is the bug. Both requests can read "open" before either writes, and both think they got the slot.

### The solution: one atomic conditional UPDATE

Booking is a single statement that checks and writes together:

```sql
UPDATE slots SET status = 'claimed' WHERE id = :slot_id AND status = 'open'
```

Postgres locks the row for the first request. The second request waits, and when the first commits, it re-checks the `WHERE` condition against the updated row. `status = 'open'` is now false, so it updates zero rows. The check can only run after the first result is visible, so there is no gap.

The result is detected with SQLAlchemy's `rowcount`:

- `rowcount == 1` means the booking succeeded.
- `rowcount == 0` means the slot was not available.

### Same client double-tap (idempotency)

When `rowcount == 0`, the code fetches the booking and compares its client ID to the client making the request (from the JWT).

- **Same client:** treated as success. A double-tap or a slow UI should not show an error.
- **Different client:** an "already claimed" error with HTTP **409 Conflict**. The request is valid, but the current state of the slot makes it impossible.

### Why slots are pre-generated

Booking is an `UPDATE` on a row that already exists. A row that exists can be locked. If slots were created at booking time (an `INSERT`), two requests could both find nothing and both insert, with no row to lock. Pre-generating slots turns "create a booking" into "claim an existing row."

### Cancellation

Cancel is also one conditional UPDATE. Its `WHERE` clause checks the booking's state (`confirmed`) and ownership:

- **Client:** the booking's client ID must match the requester's client ID.
- **Barber:** the Barber row is looked up from the JWT user ID, and the booking's barber ID must match that Barber's ID.

A second cancel on the same booking finds it already cancelled and updates zero rows. The booking change and the slot release (back to `open`) happen in **one transaction with a single commit**, so a failure in the middle rolls back both. This prevents a cancelled booking with a slot that stays blocked forever.

### Verification

Four concurrency tests run against a real Postgres database using `asyncio.gather`, so the locking behavior is tested on the same kind of database used in production.

## Authentication and roles

- **JWT payload:** user ID and role. The token is **signed, not encrypted**: anyone holding it can read the payload, but nobody can change it without the secret key, because the server recomputes the signature and compares.
- **Secret key:** used by the server to sign and verify tokens. It is never in the token and never in the code.
- **Token lifetime:** access tokens expire after 3600 seconds (1 hour).
- **State is checked in the database, not the token.** `is_active` and `is_owner` can change after a token is issued, so protected endpoints read them fresh from the database (`require_active_client`, `require_active_barber`).

### Roles

| Role | Can do |
|---|---|
| **Client** | Book slots, cancel their own bookings. |
| **Barber** | Cancel bookings that belong to them. Updates their own profile through a restricted schema that has no `is_owner` or `is_active` field, so a barber cannot promote or reactivate themselves. |
| **Owner** (a barber with `is_owner = true`) | View shop-wide data, register new barbers, close the shop, and manage barbers through a separate owner schema. |

Owner checks work in two layers: `_verify_ownership` proves the requester owns the shop, then the target barber is looked up inside that shop. The first barber of a new shop gets `is_owner = true` at shop registration.

## Setup

```bash
git clone <your-repo-url>
cd <repo-folder>

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

Create a `.env` file (copy `.env.example`) and fill in your own values:

```env
DATABASE_URL=postgresql://user:password@host/dbname
SECRET_KEY=generate-your-own-long-random-value
ALGORITHM=HS256
```

- `DATABASE_URL`: you need your own Postgres database. A free Neon database works.
- `SECRET_KEY`: generate your own. Never reuse a key from another deployment.

Apply the migrations and start the server:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

Swagger docs are at `http://127.0.0.1:8000/docs`.

## Deployment

- **API:** Railway.
- **Database:** Neon, using the **direct (unpooled)** connection string. The app is small, so connection limits are not a concern, and direct connections work better with migrations. A pooled connection is a possible change if connection limits ever become a problem.
- **Secrets** (database URL, JWT secret) live in Railway's environment variables. Locally they live in `.env`, which is listed in `.gitignore`.

## Testing

- 6 automated tests on the security-critical paths: wrong password, invalid JWT on a protected endpoint, a client reading another client's data, a barber acting on another shop's resource, a deactivated account on a protected endpoint, and a client cancelling another client's booking.
- 4 separate concurrency tests against a real database (see above).
- CI runs through GitHub Actions.

The security paths were tested first because a bug there is a security hole, not a cosmetic issue. Most other workflows were tested manually.

## Known limitations (MVP cuts)

These were cut on purpose to ship a working MVP:

- **No server-side token revocation and no refresh tokens.** A stolen token works until it expires (at most 1 hour), or until the account is deactivated. Users must log in again every hour.
- **No new-login verification.** It was cut because it adds real complexity (device tracking, emails, codes) and its impact was not fully weighed at the time. Anyone who learns a user's password can log in and act as that user. For a barber, that means cancelling their bookings. For an owner, it also means closing the shop. Client accounts hold only a name and email.
- **Login does not check `is_active`.** A deactivated user can receive a token, but every protected endpoint rejects it.
- **Nightly slot job has no retry or catch-up.** If a night fails, the 14-day window shrinks by one day.
- **Ownership cannot be removed or transferred.** An owner cannot be deactivated or demoted through the owner update endpoint, to prevent a shop with no owner.
- **Limited automated test coverage.** Full coverage is planned.

## What's next (V2)

1. **New-login verification**, because a stolen password currently gives full access.
2. **Refresh tokens with server-side revocation**, so sessions can be ended early and users do not have to log in every hour.

Later ideas: releasing the slot automatically when a client does not show up, a front end or Telegram bot on top of the API, and a login check for `is_active`.
