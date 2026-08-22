# Dayflow HRMS

**Dayflow** is a Human Resource Management System (HRMS) built with a modern, standalone architecture using **FastAPI**, **PostgreSQL**, and **React + TypeScript**. The system digitises core HR workflows — employee onboarding, attendance tracking, leave management, payroll, and audit logging — with strict role-based access control enforced server-side at every layer.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [Role & Permission Model](#role--permission-model)
- [Key Business Rules](#key-business-rules)
- [Getting Started](#getting-started)
- [Running Tests](#running-tests)
- [Environment Variables](#environment-variables)
- [Development Notes](#development-notes)

---

## Architecture Overview

```
React + TypeScript (Frontend)
        │
        ▼
FastAPI (REST API Layer)
        │
        ▼
PostgreSQL (Database — standalone schema, no ORM)
```

**No ORM is used in the standalone backend.** The database schema is defined entirely in `database/schema.sql` as raw PostgreSQL DDL. All queries are written against this schema using a raw SQL driver (`psycopg2`).

Business logic lives in a dedicated **service layer**, not inside route handlers. Routes are thin: parse request → call service → return response.

---

## Technology Stack

| Layer      | Technology                         |
|------------|------------------------------------|
| Database   | PostgreSQL 17+ (standalone DDL)    |
| API        | FastAPI (Python 3.12+)             |
| DB Driver  | psycopg2                           |
| Frontend   | React + TypeScript                 |
| Auth       | JWT (HS256) — custom implementation|
| Testing    | pytest + psycopg2                  |

> **Note:** The `app/` directory and `alembic/` directory contain a legacy SQLAlchemy-based implementation from an earlier prototype. They are preserved for reference but are **not** part of the current standalone architecture.

---

## Project Structure

```
Oodoo_Human_Resource_Management/
├── database/
│   └── schema.sql              # Standalone PostgreSQL DDL — source of truth
├── docs/
│   ├── architecture.md         # Architecture decisions
│   ├── database-design.md      # ERD and table design rationale
│   ├── permission-matrix.md    # Role-based access control matrix
│   └── workflows.md            # Workflow test case specifications
├── tests/
│   ├── test_database.py        # SQLAlchemy ORM layer tests (legacy prototype)
│   ├── test_schema_sql.py      # Static schema.sql structure validation
│   └── test_postgres_integration.py  # Live PostgreSQL constraint & trigger tests
├── dayflow_hrms/               # Odoo module (separate, not the standalone backend)
├── app/                        # Legacy FastAPI + SQLAlchemy prototype (preserved)
├── alembic/                    # Legacy Alembic migrations (preserved)
├── pytest.ini                  # pytest configuration
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

---

## Database Schema

The canonical database schema lives at [`database/schema.sql`](database/schema.sql).

### Tables

| Table               | Purpose                                                              |
|---------------------|----------------------------------------------------------------------|
| `users`             | Authentication — email, password hash, role (`Employee` / `HR`)     |
| `departments`       | Department list; supports circular manager reference to `employees`  |
| `employees`         | Core HR profile; 1:1 with `users`                                   |
| `attendance`        | Daily check-in / check-out records per employee                      |
| `leave_types`       | Leave category lookup: Paid, Sick, Unpaid, etc.                     |
| `leave_requests`    | Employee leave applications with HR review trail                     |
| `salary_structures` | Time-bound salary components per employee                            |
| `payslips`          | Immutable monthly salary snapshots                                   |
| `employee_documents`| Employee document storage paths (no binary blobs)                   |
| `audit_logs`        | System audit trail with `JSONB` detail payload                       |

### Schema Highlights

- **Identity PKs** — All tables use `GENERATED ALWAYS AS IDENTITY PRIMARY KEY` (PostgreSQL native).
- **Timestamps** — All mutable tables carry `created_at TIMESTAMPTZ` and `updated_at TIMESTAMPTZ`, with automatic trigger-based refresh on update.
- **Monetary values** — All salary/payslip amounts use `NUMERIC(12,2)` to avoid floating-point rounding errors.
- **Partial unique index** — `salary_structures` enforces at most one active structure per employee (`WHERE effective_to IS NULL`).
- **Circular FK** — `departments.manager_id → employees.id` is added via `ALTER TABLE` after `employees` is created, resolving the circular dependency cleanly.
- **`ON DELETE RESTRICT`** — Applied on all historical/financial tables to protect audit integrity.

---

## Role & Permission Model

Two roles exist: `Employee` and `HR`.

| Resource            | Employee                     | HR                        |
|---------------------|------------------------------|---------------------------|
| Own employee profile| Read + edit limited fields   | Full CRUD                 |
| Other profiles      | ❌ Blocked                   | Read + edit               |
| Own attendance      | Check-in / check-out         | Full management           |
| Other attendance    | ❌ Blocked                   | Full management           |
| Own leave requests  | Submit, edit (pending only)  | Full management           |
| Leave approval      | ❌ Blocked                   | Approve / Reject          |
| Own salary structure| Read-only                    | Full management           |
| Own payslips        | Read-only                    | Generate + read           |
| Departments         | Read-only                    | Full CRUD                 |
| Audit logs          | ❌ No access                 | Read-only                 |

> **Critical principle:** All permission checks are enforced in the **service layer** via JWT decoding and ownership comparison — never in the frontend alone and never by trusting an `employee_id` from the request payload.

---

## Key Business Rules

### Attendance
- One record per employee per calendar day (`UNIQUE(employee_id, attendance_date)`).
- `check_out` must be strictly after `check_in` (database-level `CHECK` constraint).
- Attendance status (`Present`, `Absent`, `Half-day`, `Leave`) is derived by the service layer, not stored as a redundant field.

### Leave Requests
- `start_date` must be ≤ `end_date` (database-level `CHECK` constraint).
- Leave status values are constrained to `Pending`, `Approved`, `Rejected`.
- On approval, the service layer synchronises the leave date range into `attendance` records.
- Employees may edit only their own **pending** leave requests; approved requests are immutable to employees.

### Salary Structures
- At most one **active** salary structure per employee (partial unique index on `effective_to IS NULL`).
- Creating a new structure should close the previous one by setting `effective_to`.
- All monetary amounts must be non-negative (database-level `CHECK` constraints).

### Payslips
- `UNIQUE(employee_id, month, year)` — one payslip per pay period.
- Payslips are **immutable snapshots** — salary field values are copied at generation time and never updated, even if the underlying salary structure changes.

---

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL 17+

### Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Initialise the database

Create a PostgreSQL database and run the schema:

```bash
createdb dayflow_hrms
psql -d dayflow_hrms -f database/schema.sql
```

### Configure connection

Copy and edit the environment file:

```bash
cp .env.example .env
# Edit .env and set DATABASE_URL
```

---

## Running Tests

```bash
# All standalone tests (no Odoo required)
pytest -v

# PostgreSQL integration tests only
pytest -v tests/test_postgres_integration.py
```

### Test Suites

| File                            | Type                  | Tests | Description                                              |
|---------------------------------|-----------------------|-------|----------------------------------------------------------|
| `test_schema_sql.py`            | Static analysis       | 6     | Validates schema.sql structure and constraint presence   |
| `test_postgres_integration.py`  | Live PostgreSQL tests  | 14    | Executes schema against real PG; verifies all constraints |
| `test_database.py`              | Legacy ORM tests      | 2     | SQLAlchemy model tests (legacy prototype; preserved)     |

The integration tests automatically spin up an ephemeral PostgreSQL instance if no server is available on the standard socket. Each test runs against a clean schema (dropped and recreated per test).

---

## Environment Variables

| Variable        | Default                                          | Description                        |
|-----------------|--------------------------------------------------|------------------------------------|
| `DATABASE_URL`  | `postgresql://postgres:postgres@localhost/dayflow_hrms` | PostgreSQL connection string  |
| `TEST_DATABASE_URL` | _(falls back to `DATABASE_URL`)_           | Override for test database         |

---

## Development Notes

- **`dayflow_hrms/`** — The Odoo custom module is preserved in this repository. It implements the same HRMS domain using the Odoo ORM and is independent of the standalone backend. It requires an Odoo server to run its tests (`dayflow_hrms/tests/` are Odoo-only and excluded from standalone pytest via `pytest.ini`).
- **`app/`** and **`alembic/`** — Legacy SQLAlchemy/Alembic prototype files. Preserved for reference; not part of the current implementation path.
- **No Docker** — The standalone PostgreSQL schema is the only infrastructure dependency. A local PostgreSQL server is sufficient for development and testing.
