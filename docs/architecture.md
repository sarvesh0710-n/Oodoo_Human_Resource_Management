# Dayflow HRMS — Architecture

## Overview

Dayflow is a standalone HRMS built for an 8-hour hackathon. It digitizes
employee onboarding, profile management, attendance, leave management,
and payroll visibility, with strict role-based access control enforced
server-side.

Stack: **FastAPI (backend/API) + PostgreSQL (database) + SQLAlchemy (ORM)**.
No framework-provided auth/HR models — everything (including auth) is a
custom table designed and owned by this project.

## Dependencies (minimal 3rd-party)

- FastAPI — API layer
- SQLAlchemy — ORM / schema definition
- Alembic — versioned migrations
- passlib/bcrypt (or equivalent) — password hashing
- python-jose (or similar) — JWT session auth
- Jinja2 — server-rendered frontend templates (avoids a separate JS
  framework given no prior frontend experience)

No external HR/auth-as-a-service APIs. Email verification, if implemented,
uses a minimal SMTP call — not a paid third-party provider.

## Layers

```
Frontend (Jinja2 templates + CSS)
   |
API layer (FastAPI routers)          -- request validation, routing
   |
Service layer (business logic)       -- leave approval, payroll calc,
   |                                     attendance rules, permission checks
Data access layer (SQLAlchemy models)
   |
PostgreSQL
```

Business logic lives in a dedicated service layer, not inside route
handlers — this is what "modularity" scoring is checking for. Routes stay
thin: parse request, call service, return response.

## Authentication & Authorization

- `USER` table owns identity: email, password_hash (bcrypt), role,
  is_verified, is_active.
- JWT-based auth. Token carries user id + role.
- **Every protected endpoint checks role/ownership server-side**, not just
  in the frontend. A frontend hiding a button is not authorization — this
  is the explicit hackathon requirement and the main security-scoring axis.
- Ownership checks: an Employee can only fetch/modify rows where the
  target row's `employee_id` resolves to their own `EMPLOYEE.id` (never
  trust an `employee_id` passed in a request body/query — derive it from
  the authenticated user's token, then compare against the row).

## Models

| Table | Purpose |
|---|---|
| `USER` | Authentication only — email, password_hash, role, verification |
| `EMPLOYEE` | Core HR record — 1:1 with USER, department, job title, manager |
| `DEPARTMENT` | Normalized department list |
| `ATTENDANCE` | Daily check-in/check-out per employee |
| `LEAVE_TYPE` | Paid / Sick / Unpaid lookup |
| `LEAVE_REQUEST` | Employee leave applications + admin review trail |
| `SALARY_STRUCTURE` | Time-bound salary components per employee |
| `PAYSLIP` | Immutable monthly snapshot generated from a salary structure |
| `AUDIT_LOG` | Lightweight trail of sensitive actions |

Full field-level spec lives in `database-design.md`.

## Attendance status

Stored (`Present`/`Absent`/`Half-day`/`Leave`) but computed by the service
layer at check-in/check-out/leave-approval time, not left for the frontend
to infer. Avoids two sources of truth while still letting simple reads
show status without recomputing it every time.

## Leave → Attendance sync

On leave approval, the service layer upserts `ATTENDANCE` rows for each
date in the leave's range with `status = 'Leave'`, so attendance and leave
records never drift out of sync.

## Payroll design rationale

`PAYSLIP` stores a **snapshot** of salary fields at generation time, not a
live reference to `SALARY_STRUCTURE`. If salary changes in March, the
January payslip must still show January's numbers.

## Frontend / UX

- Role-specific navigation (Employee vs Admin/HR), rendered based on the
  authenticated user's role — UX only; the API independently enforces the
  same restriction.
- Server-rendered Jinja2 pages: Dashboard, My Profile, Attendance, Leave,
  Payroll (Employee) / Employees, Attendance, Leave Approvals, Payroll,
  Reports (Admin/HR).

## Scalability talking points

- Pagination on list endpoints (attendance history, employee list) instead
  of loading full tables.
- Indexes on frequently-queried FK/lookup columns (`employee_id`, `date`,
  `status`, `email`).
- Stateless API (JWT, no server-side session store) — horizontally
  scalable without sticky sessions.
- Historical salary/payslip data never mutated in place — safe to cache.

## Git workflow

Feature branches per module (auth, attendance, leave, payroll), meaningful
commit messages (`feat:`, `fix:`, `chore:` prefixes), clean main branch at
submission.
