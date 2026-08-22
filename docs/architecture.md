# Dayflow HRMS — System Architecture

This document describes the architectural layout, core components, security layer, and design system of **Dayflow HRMS**.

---

## 🏛️ Layered System Architecture

Dayflow HRMS is built using a strict **Layered Architecture Pattern** to separate concerns between HTTP presentation, business logic execution, data persistence, and UI rendering:

```text
[ Web Browser / Client ]
           │
           ▼
[ FastAPI Web Router (app/web/views.py) ]  ───► [ Jinja2 Templates (app/templates/*) ]
           │
           ▼
[ FastAPI REST Router (app/api/*.py) ]
           │
           ▼
[ Security & Dependency Layer (app/core/deps.py) ]
           │
           ▼
[ Domain Service Layer (app/services/*.py) ]
           │
           ▼
[ Data Access Layer (SQLAlchemy 2.0 ORM) ]
           │
           ▼
[ Database (PostgreSQL / SQLite fallback) ]
```

---

## 🔧 Core Architectural Components

### 1. Presentation & Routing Layer (`app/api/` & `app/web/`)
- **JSON REST APIs (`app/api/`)**: RESTful endpoints providing JSON responses for mobile/SPA/external integration. Auth token verification is injected on every request via FastAPI's `Depends(get_current_user)`.
- **Web UI Routes (`app/web/views.py`)**: Server-side HTML page rendering powered by Jinja2 templates. Decodes JWT tokens from `access_token` cookies to route users to role-specific dashboards.

### 2. Domain Service Layer (`app/services/`)
- Pure Python domain logic modules isolated from HTTP request/response details.
- Handles complex business workflows:
  - **Attendance Calculation**: Shift duration validation (`check_out > check_in`).
  - **Leave Management**: Overlap checking (`start_date <= existing.end_date AND end_date >= existing.start_date`) and attendance auto-sync upon approval.
  - **Payroll Engine**: Compensation snapshotting, effective date closing, and idempotent payslip generation.
  - **Self-Action Guards (`app/services/guards.py`)**: `SEC-13` assertions ensuring HR Admins cannot approve their own leaves or generate their own payslips.

### 3. Security & Authentication Layer (`app/core/`)
- **Authentication**: OAuth2 Password Flow with JSON Web Tokens (JWT) signed via `HS256`.
- **Password Protection**: Salted `bcrypt` password hashing via `passlib`.
- **Fail-Fast Configuration**: `app/core/security.py` validates that `SECRET_KEY` is explicitly set in `.env` or environment during startup. If missing, it raises a `RuntimeError` unless `DAYFLOW_ENV=dev` is active.

### 4. Persistence Layer (`app/models/` & `app/core/database.py`)
- **ORM Engine**: SQLAlchemy 2.0 declarative models.
- **Database Support**: Native PostgreSQL connection via `psycopg2-binary`, with automatic fallback to local `SQLite` (`sqlite:///dayflow.db`).
- **Migrations**: Database schema versioning managed via **Alembic**.

---

## 🎨 UI Design System Architecture

The frontend styling in [`app/static/style.css`](../app/static/style.css) follows an **Organic Windows Green** aesthetic:

- **Color System**:
  - Primary Dark Green: `#14382B`
  - Primary Brand Green: `#1E4D3B`
  - Accent Muted Green: `#2A6B53`
  - Light Background: `#E8F2EE`
  - Warning Red: `#8B2020`
- **Zero Gradients**: Pure solid colors for high contrast, rapid rendering, and enterprise readability.
- **Typography**: Clean geometric sans-serif (`Inter`) with strict scale (`0.75rem` to `1.5rem`).
- **Standard Controls Padding**: Inputs (`7px 10px`), Buttons (`8px 14px`), Tables (`8px 12px`).
- **Mobile Responsive Drawer**: Off-canvas navigation menu (`#app-sidebar.mobile-open`) triggered by a mobile hamburger button (`.mobile-toggle`).

---

## 👥 Role-Based Access Control (RBAC) Architecture

Dayflow HRMS enforces a strict **Two-Role Model**:

1. **`employee`**: Standard company staff member.
   - Access limited strictly to own employee records, attendance history, leave requests, and payslips.
   - Server-side token resolution derives identity directly from `current_user.id`, ignoring client-passed `employee_id` parameters.
2. **`admin_hr`**: Combined HR & Administrator role.
   - Full read/write access across all company employees, departments, attendance logs, leave approvals, and payroll structures.
   - Enforced by `SEC-13` peer-approval guard: blocked from performing administrative actions (leave approval, salary structure setup, payslip generation) on their own record.
