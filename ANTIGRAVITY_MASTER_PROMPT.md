# MASTER CONTEXT — Dayflow HRMS: Odoo Removal → Production Standalone HRMS

Repository: `https://github.com/sarvesh0710-n/Oodoo_Human_Resource_Management`

You are acting as a senior engineer taking over this repository. This document
has already been ground-truthed against the actual repo contents (not just a
README) as of the current commit. Do not re-discover facts stated here as
"VERIFIED" — trust them and move straight to planning. Do re-verify anything
marked "CONFIRM" before acting on it, since repo state can move between now
and when you run.

The end goal: a professional, production-quality, standalone HRMS. Odoo is
being fully removed and NOT replaced with another ERP framework.

---

## 0. VERIFIED CURRENT STATE (read this before touching anything)

**What actually exists and works:**
- `database/schema.sql` — the real, mature source of truth for the standalone
  DB. 10 tables (`users`, `departments`, `employees`, `attendance`,
  `leave_types`, `leave_requests`, `salary_structures`, `payslips`,
  `employee_documents`, `audit_logs`). Identity PKs, `NUMERIC(12,2)` money,
  `updated_at` triggers, a resolved circular FK (`departments.manager_id` ↔
  `employees.id`), a partial unique index enforcing one active salary
  structure per employee, `ON DELETE RESTRICT` on financial/historical
  tables, and sensible indexes. **This is good, tested work — do not rewrite
  it from scratch or replace it with an ORM-generated schema.**
- `tests/test_schema_sql.py` (6 static tests) and
  `tests/test_postgres_integration.py` (14 live-PostgreSQL tests, spins up an
  ephemeral PG instance if needed) — both pass against `schema.sql` today.
  Keep these; extend, don't replace.
- `docs/permission-matrix.md` — a complete, correct RBAC spec for
  Employee/HR across every table (Employee, Attendance, Leave, Salary
  Structure, Payslip, Department, Audit Log), including the exact
  server-side enforcement pattern (`get_current_user` dependency + explicit
  per-route ownership check). **Use this as the authoritative permission
  spec. Do not re-derive RBAC rules from first principles — implement
  against this doc, and only edit it if implementation reveals a genuine gap
  or contradiction.**
- `docs/workflows.md` — a complete test-case matrix (`ATT-01..08`,
  `LEAVE-01..09`, `SEC-01..13`) written for FastAPI's `TestClient`.
  **Use this as the authoritative test spec for the security/integration
  test suites you write. Implement every case listed; do not invent a
  different set of cases.**

**What does NOT exist yet (build all of this):**
- No FastAPI application at all — no `main.py`, no routers, no service
  layer, no repository layer, no Pydantic schemas, no auth implementation
  (no password hashing, no JWT, nothing).
- No frontend of any kind. No `frontend/` directory, no React, no npm
  project. This is a from-scratch build.
- No Docker, no `docker-compose.yml`, no reverse proxy config.
- No CI/CD — no `.github/workflows/`.
- `requirements.txt` currently only has `fastapi`, `sqlalchemy>=2.0`,
  `alembic`, `psycopg2-binary`, `python-dotenv` — **no password hashing
  library (argon2-cffi or bcrypt/passlib) and no JWT library
  (pyjwt/python-jose) are installed yet.** Add them.
- `.env.example` currently has one line (`DATABASE_URL`). Needs JWT secret,
  token lifetimes, CORS origins, etc.
- `docs/decisions.md`, `docs/er-diagram.md`, `docs/README.md` are empty
  placeholder files.

**Dead/legacy code to deal with (see Section 1):**
- `app/` + `alembic/` + `alembic.ini` — a legacy SQLAlchemy prototype
  (`User`, `Department`, `Employee`, `Attendance`, `LeaveType`,
  `LeaveRequest`, `SalaryStructure`, `Payslip`, `AuditLog` models mirroring
  `schema.sql`). CONFIRM, but as of inspection this is only imported by
  `tests/test_database.py` and nothing else — it is not wired into any
  running application.
- `dayflow_hrms/` — a real, functioning Odoo 17 custom addon (depends on
  Odoo's `base`, `hr`, `hr_attendance`, `hr_holidays`). Fully isolated:
  CONFIRM, but as of inspection the only references to "Odoo" outside this
  folder are prose mentions in `README.md` and `docs/database-design.md` —
  no code elsewhere imports or depends on it.

**A decision already made by the repo that you must respect:**
README.md states explicitly: *"No ORM is used in the standalone backend...
All queries are written against this schema using a raw SQL driver
(psycopg2)."* This is the current direction and it conflicts with an
older, stale plan in `docs/architecture.md` (which describes Jinja2
templates + SQLAlchemy — written for an earlier 8-hour-hackathon framing).

**Resolution: follow README + `schema.sql`, not `docs/architecture.md`.**
Build the standalone backend as FastAPI + raw `psycopg2` (or `psycopg3`) +
a hand-written repository layer with parameterized SQL, NOT SQLAlchemy.
Rewrite `docs/architecture.md` to match this reality once the backend
exists, instead of leaving two contradictory architecture descriptions in
the repo.

---

## 1. STEP ZERO — VERIFICATION BEFORE ANY CHANGE

Before writing a line of new application code:

1. Re-run the CONFIRM items above: `grep -ri odoo` across the repo outside
   `dayflow_hrms/`; check for any import of `app.*` outside
   `tests/test_database.py`; check for any `.github/`, `docker*`, or
   `.env` files that may have been added since this document was written.
2. Run the existing test suite (`pytest -v`) against a real or ephemeral
   Postgres instance and confirm the 20 schema/integration tests still
   pass. Do not proceed on the assumption they pass — verify.
3. Produce a short written gap analysis (target vs. actual, using Section 0
   as your baseline) and a phased migration/implementation plan before
   generating code. Do not skip straight to scaffolding.

Do not delete anything destructively in one pass. Sequence:
**Understand → Plan → Implement → Test → Security test → Review.**

---

## 2. ODOO REMOVAL

Once confirmed isolated (Step 1.1):

- Delete `dayflow_hrms/` in full (models, views, security, data, static,
  tests, manifest, `__init__.py`).
- Remove the Odoo-related prose in `README.md` and `docs/database-design.md`
  (the "Development Notes" section referencing `dayflow_hrms/`, and any
  table describing it as a parallel implementation).
- Grep the whole repo again after deletion to confirm zero remaining
  `odoo`/`Odoo`/`dayflow_hrms` references.
- Do not leave a dangling mention in `pytest.ini`'s `norecursedirs` once
  the directory is gone.

## 3. LEGACY SQLALCHEMY PROTOTYPE (`app/`, `alembic/`, `alembic.ini`)

Given the repo's own decision to go raw-SQL/no-ORM (Section 0), this
prototype now duplicates `schema.sql` in a second, divergent form and adds
no value — but confirm before deleting:

1. Grep for any import of `app.` or `alembic` outside `tests/test_database.py`
   and the `app`/`alembic` directories themselves.
2. If genuinely unused (expected outcome): delete `app/`, `alembic/`,
   `alembic.ini`, `tests/test_database.py`, and drop `sqlalchemy`/`alembic`
   from `requirements.txt`. Remove the "legacy prototype" caveats from
   `README.md` since there will be nothing left to caveat.
3. If you find it's used somewhere unexpected, stop and report that instead
   of deleting — don't guess.

This keeps exactly one schema definition (`database/schema.sql`) as the
single source of truth, which is easier to keep correct than two.

---

## 4. TARGET ARCHITECTURE

```
React + TypeScript + Vite + Tailwind (frontend/)
        │  HTTPS
        ▼
FastAPI (backend/app/api/v1/...)          — thin routers only
        │
        ▼
Service layer (backend/app/services/)     — business rules, workflows
        │
        ▼
Repository layer (backend/app/repositories/) — parameterized psycopg2 SQL
        │
        ▼
PostgreSQL (database/schema.sql is authoritative DDL)
```

No SQLAlchemy, no ORM, no Alembic for the standalone path (that decision is
already made — see Section 0). Schema changes are hand-written, reviewed SQL
migration files layered on top of `database/schema.sql` (a simple
`database/migrations/NNN_description.sql` convention is sufficient; do not
introduce a migration framework just to have one).

**Backend stack:** Python 3.12+, FastAPI, Pydantic v2 for request/response
schemas, psycopg2 (or psycopg3) for the data layer, `argon2-cffi` (preferred)
or `bcrypt` via `passlib` for password hashing, `pyjwt` or `python-jose` for
JWT, `pytest` + `httpx`/`TestClient` for tests.

**Frontend stack:** React + TypeScript + Vite + Tailwind CSS, built from
scratch — reusable components, no framework-provided admin scaffolding.

**Do not introduce:** Odoo, Django Admin, ERPNext, another ERP framework,
Kubernetes, Kafka, Redis without a demonstrated need, or a microservice
split. This is a modular monolith: one backend, one frontend, one Postgres
database, clear internal domain boundaries.

---

## 5. DOMAIN & ROLES (already specified — implement, don't redesign)

Two roles only, exactly as `docs/permission-matrix.md` defines: **Employee**
and **HR**. Do not add an Admin role unless a real requirement emerges.
Implement the matrix as written, table by table (Employee, Attendance,
Leave Request, Salary Structure, Payslip, Department, Audit Log), enforced
server-side via a `get_current_user` dependency plus an explicit
ownership/role check inside every route or service function that touches
employee-scoped data — never via a single global middleware that could be
forgotten on one route, and never via hiding a frontend button.

Core modules to build against the existing schema: Users/Auth, Employees,
Departments, Attendance, Leave, Payroll (salary structures + payslips),
Employee Documents, Audit Logs, Dashboard/Reports.

State machines to implement exactly as `docs/workflows.md` and the schema's
CHECK constraints imply:
- **Leave:** `Pending → Approved` / `Pending → Rejected` only. No
  `Rejected → Approved` or `Approved → Pending`. Use an atomic
  `UPDATE ... WHERE status = 'Pending'` so concurrent HR approvals can't
  both win.
- **Payslip:** generated once per `(employee_id, month, year)` (already a
  DB unique constraint), immutable after generation — snapshot the salary
  fields at generation time, never re-point at a live `salary_structures`
  row. Corrections happen via a new adjustment record, not an in-place edit.
- **Attendance:** one row per `(employee_id, attendance_date)` (already a
  DB unique constraint), `check_out` must be strictly after `check_in`
  (already a DB CHECK constraint) — the service layer must not trust
  client-supplied timestamps for either; use `CURRENT_TIMESTAMP` / server
  time. Leave approval must sync into `attendance` (upsert rows for the
  leave's date range) inside the same transaction as the approval.

---

## 6. TEST SPEC — IMPLEMENT `docs/workflows.md` VERBATIM

`docs/workflows.md` already enumerates the required test cases
(`ATT-01..08`, `LEAVE-01..09`, `SEC-01..13`) with expected status codes and
outcomes. Build `tests/security/test_security.py`,
`tests/integration/test_attendance.py`, and
`tests/integration/test_leave.py` to implement exactly these cases against
a real `TestClient` + seeded Postgres — not a mocked one, since the point
(per the doc's own coverage notes) is proving server-side enforcement can't
be bypassed via a manipulated `employee_id` or a hidden frontend control.

Beyond that spec, also cover:
- Mass assignment (client cannot set `role`, `salary`, `is_admin` via a
  generic update payload — use narrow Pydantic schemas per operation:
  `EmployeeUpdate`, `UserRoleUpdate`, `SalaryUpdate`, etc.)
- SQL injection (every repository query is parameterized — never an
  f-string into `psycopg2.execute`)
- Path traversal / file-type / size limits on employee document uploads
- Expired/invalid/deactivated-user JWTs rejected on every protected route
- Rate limiting on `/login`, `/refresh`, and any password-reset endpoint
- One E2E flow (Playwright): employee submits leave → logs out → HR logs
  in → approves → employee logs back in → sees `Approved` status and
  synced attendance.

Keep `test_schema_sql.py` and `test_postgres_integration.py` as-is (they
already pass); add new suites alongside them under `tests/unit/`,
`tests/integration/`, `tests/security/`, `tests/e2e/` rather than
restructuring what already works.

---

## 7. SECURITY BASELINE (non-negotiable, apply everywhere)

- Every sensitive request: security headers/CORS → rate limiting →
  authentication → authorization → ownership check → input validation →
  business rules → service layer → DB transaction → audit event → response.
- Passwords: Argon2id or bcrypt only, never SHA-256 for password storage.
- JWT: short-lived access tokens, refresh-token rotation with revocation,
  restricted signing algorithms, validated claims.
- CORS: explicit trusted origins, never `allow_origins=["*"]` with
  credentials.
- CSRF protection on state-changing endpoints if cookie-based auth is used.
- IDOR: `GET /employees/{other_id}`, `/attendance/{other_id}`,
  `/leave/{other_id}`, `/payroll/{other_id}`, `/documents/{other_id}`,
  `/payslips/{other_id}` must all fail for an Employee token that doesn't
  own that ID — this is what SEC-02/06/13 in `docs/workflows.md` test.
- Employee documents: authenticated + authorized upload only, size/MIME
  validation, server-generated random filenames, private storage, no
  user-controlled filesystem paths.
- Audit log every: login, employee create/update, salary changes, leave
  approval/rejection, attendance corrections, payroll generation/
  finalization, document access, permission changes, and security-relevant
  failures. Audit logs are append-only — no update/delete path for normal
  HR users.
- Never expose raw exceptions (e.g. `psycopg2.errors.UniqueViolation`) to
  clients — map to structured `{error: {code, message, request_id}}`
  responses; log internals server-side.
- Attach a request ID (`X-Request-ID`) to every request, log line, error,
  and audit event for traceability.

---

## 8. OBSERVABILITY, DEPLOYMENT, CI/CD (build from scratch — none exists)

- Structured logging (`INFO`/`WARNING`/`ERROR`/`SECURITY`/`AUDIT` levels),
  basic metrics (request count, latency, error rate, DB latency, login
  failures), `GET /health` (liveness) and `GET /ready` (dependency check).
- Docker Compose for local dev: `frontend`, `backend`, `postgres` services.
  Caddy or Nginx in front for the production topology
  (Internet → HTTPS → reverse proxy → {frontend, FastAPI} → PostgreSQL).
- `.env.example` needs expanding beyond `DATABASE_URL` to cover JWT secret,
  access/refresh token TTLs, CORS allowed origins, and any storage path for
  documents — never commit real secrets.
- `.github/workflows/` CI: lint → format check → type check → unit tests →
  integration tests → security tests → frontend build → Docker build, gating
  deploy on all passing.

---

## 9. DOCUMENTATION TO UPDATE (not all from scratch — most already exists)

- **Keep as-is, treat as authoritative:** `docs/permission-matrix.md`,
  `docs/workflows.md`.
- **Rewrite to match reality:** `docs/architecture.md` (currently describes
  the stale Jinja2/SQLAlchemy plan — replace with the FastAPI +
  raw-SQL/psycopg2 + React architecture actually being built).
- **Fill in (currently empty):** `docs/decisions.md` (record the "raw SQL,
  no ORM" decision and the Odoo/legacy-prototype removal decisions made
  here), `docs/er-diagram.md`, `docs/README.md`.
- **Add:** `docs/security.md`, `docs/threat-model.md` (payroll, employee
  PII, documents, auth, audit logs — asset / threat / attack / control /
  test, one row per asset, mapped to actual test names), `docs/API.md`,
  `docs/deployment.md`.
- **Update:** `README.md` — drop the Odoo/legacy-prototype "Development
  Notes" caveats once those are removed; add frontend setup, Docker
  instructions, and CI badge once those exist.

---

## 10. WORKING PRINCIPLES

- Do not claim something is implemented unless it exists in code — verify
  by reading the actual files, not by trusting a doc (this document
  included — re-check anything time-sensitive).
- Do not delete working, tested functionality (`schema.sql`, the 20 passing
  tests, the permission matrix, the workflow spec) just to rewrite it in a
  different style.
- Do not overengineer: no Kubernetes, no microservices, no event bus, no
  cache layer, for an HRMS of this scope.
- When something is ambiguous, read the relevant code/schema/tests to see
  how the system actually behaves before changing it — don't guess from
  README prose alone (README and `docs/architecture.md` already
  contradicted each other once; don't let that happen again).
- Definition of done, per module: implemented → unit tested → integration
  tested → security tested (against `docs/workflows.md` cases at minimum)
  → reviewed for the IDOR/mass-assignment/SQL-injection patterns in
  Section 7 → documented.
