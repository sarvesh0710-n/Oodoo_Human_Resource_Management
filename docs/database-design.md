# Dayflow HRMS — Database Design

Backend: PostgreSQL, schema owned entirely by this project via SQLAlchemy
models + Alembic migrations. No framework-provided tables.

## Entity Relationship Diagram

```mermaid
erDiagram
  DEPARTMENT ||--o{ EMPLOYEE : contains
  USER ||--|| EMPLOYEE : "is"
  EMPLOYEE ||--o{ ATTENDANCE : logs
  EMPLOYEE ||--o{ LEAVE_REQUEST : submits
  LEAVE_TYPE ||--o{ LEAVE_REQUEST : categorizes
  USER ||--o{ LEAVE_REQUEST : reviews
  EMPLOYEE ||--o{ SALARY_STRUCTURE : has
  EMPLOYEE ||--o{ PAYSLIP : receives
  SALARY_STRUCTURE ||--o{ PAYSLIP : generates
  USER ||--o{ AUDIT_LOG : performs

  USER {
    int id PK
    string employee_code UK
    string email UK
    string password_hash
    string role
    bool is_verified
    bool is_active
  }

  EMPLOYEE {
    int id PK
    int user_id FK
    int department_id FK
    int manager_id FK
    string first_name
    string last_name
    string phone
    string address
    string job_title
    date joining_date
    string profile_picture
  }

  DEPARTMENT {
    int id PK
    string name
    string description
    int manager_id FK
  }

  ATTENDANCE {
    int id PK
    int employee_id FK
    date date
    time check_in
    time check_out
    string status
  }

  LEAVE_TYPE {
    int id PK
    string name
    string description
    bool is_paid
  }

  LEAVE_REQUEST {
    int id PK
    int employee_id FK
    int leave_type_id FK
    int reviewed_by FK
    date start_date
    date end_date
    string remarks
    string status
    string review_comment
    datetime reviewed_at
    datetime created_at
  }

  SALARY_STRUCTURE {
    int id PK
    int employee_id FK
    float basic_salary
    float allowances
    float deductions
    date effective_from
    date effective_to
  }

  PAYSLIP {
    int id PK
    int employee_id FK
    int salary_structure_id FK
    int month
    int year
    float basic_salary
    float allowances
    float deductions
    float gross_salary
    float net_salary
    datetime generated_at
  }

  AUDIT_LOG {
    int id PK
    int user_id FK
    string action
    string entity
    int entity_id
    datetime timestamp
  }
```

## Table Summary (9 tables)

| Table | Purpose |
|---|---|
| `USER` | Authentication only — login, password, role, email verification |
| `EMPLOYEE` | Core HR record — 1:1 with USER, holds department, job title, manager |
| `DEPARTMENT` | Normalized department list, avoids free-text duplication |
| `ATTENDANCE` | Daily check-in/check-out records per employee |
| `LEAVE_TYPE` | Lookup table: Paid, Sick, Unpaid |
| `LEAVE_REQUEST` | Employee leave applications with admin review trail |
| `SALARY_STRUCTURE` | Time-bound salary components per employee |
| `PAYSLIP` | Immutable monthly snapshot generated from a salary structure |
| `AUDIT_LOG` | Trail of sensitive actions (salary edits, leave decisions) |

## Key design decisions

- **USER vs EMPLOYEE kept separate** — auth concerns stay isolated from
  HR data. Standard practice for any custom-built system, not tied to any
  framework's convention.
- **All operational FKs point to `EMPLOYEE.id`**, not `USER.id` —
  attendance/leave/salary/payslip are facts about an employee, not a
  login session.
- **`role` is a simple string enum** on USER (Employee / Admin-HR) — a
  separate ROLE table is overengineering for two fixed roles.
- **`department_id` is a real FK**, not free text — cheap normalization,
  real payoff (reporting, department head, filtering).
- **`job_title` stays a string** — a DESIGNATION table is unnecessary at
  this scale.
- **Salary kept as flat columns** (basic/allowances/deductions), not a
  fully normalized component table — correct tradeoff for an 8-hour build.
- **PAYSLIP is a frozen snapshot**, decoupled from SALARY_STRUCTURE
  changes — historical pay records must never silently change when salary
  structures are updated later.
- **`EMPLOYEE.manager_id`** — self-referencing FK, nullable, enables a
  lightweight org hierarchy without a separate table.
- **`AUDIT_LOG`** — generic action log, directly supports the security
  evaluation criterion; logged from the service layer on sensitive writes
  (salary changes, leave approve/reject).

## Constraints to enforce

- `UNIQUE(employee_id, date)` on `ATTENDANCE` — one record per employee
  per day.
- `UNIQUE(employee_id, month, year)` on `PAYSLIP` — one payslip per
  employee per pay period.
- `UNIQUE(user_id)` on `EMPLOYEE` — enforces the 1:1 relationship.
- `UNIQUE(email)`, `UNIQUE(employee_code)` on `USER`.
- Only one `SALARY_STRUCTURE` row per employee with `effective_to = null`
  at a time — enforced in service-layer code, not raw SQL: creating a new
  structure auto-closes the previous one.
- Row-level authorization: employees can only query their own
  `ATTENDANCE` / `LEAVE_REQUEST` / `PAYSLIP` rows — enforced in the
  service layer on every request, not just hidden in the UI.

## Business logic notes (not schema, but affects design)

- **Leave approval → attendance sync**: on approval, upsert `ATTENDANCE`
  rows for each date in the leave's range with `status = 'Leave'`, so
  attendance and leave records never drift out of sync.
- **created_at / updated_at**: explicit columns on tables that need them
  (no ORM-provided equivalent here, unlike Odoo) — add `created_at`/
  `updated_at` timestamps directly where the requirement calls for them
  (e.g. `LEAVE_REQUEST.created_at`).
- **Future enhancements** (notifications, analytics/reports) require no
  new tables — buildable as scheduled jobs or aggregation queries over
  the existing schema.
