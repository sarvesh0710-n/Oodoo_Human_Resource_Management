# Dayflow HRMS — Modern Human Resource Management System

[![Python Version](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00.svg?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Alembic](https://img.shields.io/badge/Alembic-Migrations-red.svg)](https://alembic.sqlalchemy.org/)
[![Database](https://img.shields.io/badge/Database-PostgreSQL%20%7C%20SQLite-336791.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Auth](https://img.shields.io/badge/Auth-JWT%20%2B%20HttpOnly%20Cookies-000000.svg?logo=jsonwebtokens&logoColor=white)](https://jwt.io/)
[![Design](https://img.shields.io/badge/Design-Organic%20Curved%20Green-1E4D3B.svg)](#ui-design-system)
[![Tests](https://img.shields.io/badge/Tests-50%20Passing-brightgreen.svg?logo=pytest&logoColor=white)](./docs/testing_guide.md)

**Dayflow HRMS** is an enterprise-grade, human-centric Human Resource Management System built with **FastAPI**, **SQLAlchemy 2.0**, **Alembic**, and **Jinja2 Server-Side Rendered Templates**. It provides a robust, production-ready solution to digitize all core HR operations — employee lifecycle management, department hierarchies, attendance logging, leave request workflows, salary structuring, immutable payslip generation, interactive leave analytics charts, and comprehensive audit logging.

The system is architected with a strict separation of concerns, offering both **interactive server-rendered web portals** and a **high-performance RESTful API**, secured by JWT tokens in HttpOnly cookies, granular Role-Based Access Control (RBAC), and server-side self-action peer guards.

---

## Table of Contents

- [Key Features](#key-features)
- [Web Application User Workflow](#web-application-user-workflow)
- [System Architecture](#system-architecture)
- [Database Schema & ER Diagram](#database-schema--er-diagram)
- [Technology Stack](#technology-stack)
- [UI Design System](#ui-design-system)
- [Pre-Seeded Demo Login Credentials](#pre-seeded-demo-login-credentials)
- [CLI Database Management Commands](#cli-database-management-commands)
- [Running the Application](#running-the-application)
- [Testing & Quality Assurance](#testing--quality-assurance)
- [Documentation Hub](#documentation-hub)
- [License](#license)

---

## Key Features

### 1. Enterprise Authentication & Session Security
- **OAuth2 JWT Token Authentication**: Encrypted `HS256` tokens stored in tamper-proof, secure `HttpOnly` cookies.
- **Fail-Fast Security Setup**: Enforces explicit `SECRET_KEY` configuration on startup from environment variables (`.env`).
- **CSRF & XSS Protection**: Strict cookie flags (`SameSite=Lax`), context-aware HTML escaping (`escapeHtml`), and request verification headers.
- **Password Security**: Salted `bcrypt` hashing with `passlib`.

### 2. Employee Directory & Department Showcase
- **Complete Employee Profiles**: First/last name, job title, contact information, department name showcase (e.g. *Engineering*, *Product & UX*), joining date, and avatar.
- **1:1 Auth Isolation**: Separation between authentication identity (`User`) and organizational profile (`Employee`).
- **Onboarding Modal**: Admin HR can onboard new employees directly via the directory interface.

### 3. Attendance & Shift Tracking
- **One-Click Clock-In / Clock-Out**: Streamlined daily shift tracking with timestamp validation (`check_out > check_in`).
- **Leave Guard**: Rejects check-in/check-out attempts if an employee is on approved leave today (`"Cannot check in: You are on approved leave today"`).
- **Zero-Duration Rejection**: Prevents duplicate or instantaneous check-out anomalies.
- **Monthly Attendance Calendar Grid**: Visual monthly view with month navigation controls and employee filter dropdown.

### 4. Time-Off & Leave Management
- **Leave Types & Allowances**: Pre-configured categories (Paid Time Off, Medical/Sick Leave, Unpaid Leave).
- **Date Range Overlap Prevention**: Strict server-side validation against overlapping leave windows (`start_date <= existing.end_date AND end_date >= existing.start_date`).
- **HR Review Workflow**: Review queue for HR Administrators with approval/rejection comments and audit timestamps.
- **Atomic Attendance Synchronization**: Approving a leave request automatically creates or updates the employee's attendance records to `status='Leave'` across the requested date range.

### 5. Department Leave Analytics Chart
- **Interactive Chart.js Doughnut Chart**: Displays real-time department-wise leave application totals on the HR Overview Dashboard (`GET /api/leave/analytics/department-summary`).

### 6. Payroll & Compensation Engine
- **Salary Structures**: Time-bound compensation packages with `basic_salary`, `allowances`, `deductions`, `effective_from`, and `effective_to`.
- **Automatic Versioning**: Creating a new salary structure automatically closes out previous active structures.
- **Immutable Monthly Payslips**: Generates permanent point-in-time financial snapshots (`gross_salary`, `net_salary`) unaffected by future pay adjustments.
- **Financial Bounds**: Enforces positive values, non-negative net earnings, and an upper limit ceiling (`$10,000,000.00`).

### 7. Department Management & Real-Time Edits
- Normalized departments with descriptions and assigned department heads.
- Live modal editing support via `PATCH /api/departments/{id}`.

### 8. System Audit Trail & Self-Action Guards (SEC-13)
- **`SEC-13` Peer-Approval Guard**: Safeguards (`assert_not_self_action`) preventing HR Administrators from approving their own leaves, setting their own salary structures, or generating their own payslips.
- **Audit Logging**: Captures sensitive mutations in `audit_logs` table with user identification, action type, target entity, and timestamp.

---

## Web Application User Workflow

```mermaid
graph TD
    Login[Login Portal - /login] -->|Submit Email / Code + Password| AuthEngine[FastAPI Authentication Engine]
    AuthEngine -->|Verify Bcrypt & Issue JWT| RoleCheck{Role Detection}
    
    RoleCheck -->|admin_hr| AdminDash[HR Admin Dashboard - /admin-dashboard]
    RoleCheck -->|employee| EmpDash[Employee Dashboard - /dashboard]
    
    subgraph HR Admin Operations Portal
        AdminDash --> EmpDir[Employee Directory & Staff Onboarding]
        AdminDash --> DeptMgmt[Department Management & Real-Time Edits]
        AdminDash --> LeaveAppr[Leave Approvals Queue & HR Comments]
        AdminDash --> PayrollMgmt[Salary Structuring & Bulk Payslips]
        AdminDash --> HRCal[Company Attendance Calendar & Staff Filter]
    end
    
    subgraph Standard Employee Portal
        EmpDash --> ClockWidget[1-Click Shift Clock-In / Clock-Out]
        EmpDash --> MyLeaves[Submit & Track Time-Off Requests]
        EmpDash --> MyCal[Personal Monthly Attendance Calendar]
        EmpDash --> MyPayslips[View & Print Monthly Payslip Statements]
        EmpDash --> MyProfile[Personal Profile & Contact Editor]
    end
```

---

## System Architecture

```mermaid
graph TD
    Client[Web Browser / REST Consumer] --> WebRouter[FastAPI Web Router - app/web/views.py]
    Client --> APIRouter[FastAPI REST API Router - app/api/*.py]
    WebRouter --> Jinja[Jinja2 SSR Templates - app/templates/*]
    APIRouter --> Security[Security & Dependency Injection - app/core/deps.py]
    WebRouter --> Security
    Security --> DomainServices[Domain Service Layer - app/services/*.py]
    DomainServices --> Guards[SEC-13 Self-Action Peer Guards - app/services/guards.py]
    DomainServices --> Audit[Audit Service Dispatcher - app/services/audit_service.py]
    DomainServices --> ORM[SQLAlchemy 2.0 ORM Models - app/models/*.py]
    ORM --> DB[(PostgreSQL 15+ / SQLite Database)]
```

---

## Database Schema & ER Diagram

```mermaid
erDiagram
  department ||--o{ employee : "department_id"
  user ||--|| employee : "user_id"
  employee ||--o{ attendance : "employee_id"
  employee ||--o{ leave_request : "employee_id"
  leave_type ||--o{ leave_request : "leave_type_id"
  user ||--o{ leave_request : "reviewed_by"
  employee ||--o{ salary_structure : "employee_id"
  employee ||--o{ payslip : "employee_id"
  salary_structure ||--o{ payslip : "salary_structure_id"
  user ||--o{ audit_log : "user_id"

  user {
    int id PK
    string employee_code UK
    string email UK
    string password_hash
    string role
    bool is_verified
    bool is_active
  }
  employee {
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
  }
  department {
    int id PK
    string name
    string description
    int manager_id FK
  }
  attendance {
    int id PK
    int employee_id FK
    date date
    time check_in
    time check_out
    string status
  }
  leave_type {
    int id PK
    string name
    string description
    bool is_paid
  }
  leave_request {
    int id PK
    int employee_id FK
    int leave_type_id FK
    int reviewed_by FK
    date start_date
    date end_date
    string remarks
    string status
  }
  salary_structure {
    int id PK
    int employee_id FK
    float basic_salary
    float allowances
    float deductions
    date effective_from
    date effective_to
  }
  payslip {
    int id PK
    int employee_id FK
    int salary_structure_id FK
    int month
    int year
    float gross_salary
    float net_salary
  }
  audit_log {
    int id PK
    int user_id FK
    string action
    string entity
    int entity_id
    datetime timestamp
  }
```

---

## Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | **FastAPI** (Python 3.11 / 3.12+) | High-performance ASGI web framework & routing engine |
| **Web Presentation** | **Jinja2** + **Vanilla CSS/JS** | Lightweight, reactive Server-Side Rendered (SSR) UI |
| **Charts & Analytics**| **Chart.js** | Interactive doughnut charts for department leave distribution |
| **ORM & Persistence** | **SQLAlchemy 2.0+** | Declarative data modeling, relationships, and queries |
| **Database Migrations**| **Alembic** | Reliable schema versioning and upgrade/downgrade paths |
| **Database Engines** | **PostgreSQL 15+** / **SQLite** | Production RDBMS with local zero-setup SQLite fallback |
| **Authentication** | **python-jose** + **passlib** (bcrypt)| Signed JWT tokens & salted password hashing |
| **Data Validation** | **Pydantic v2** | Request schema parsing and type validation |
| **Test Framework** | **Pytest** + **httpx** | 50 comprehensive unit, integration, and QA test cases |

---

## UI Design System

The web frontend uses a modern **Organic Curved Green** aesthetic ([`app/static/style.css`](app/static/style.css)):
- **Curved Radius System**: Deep smooth curved borders (`border-radius: 24px` for cards, `18px` for inputs/selects, `28px` for modals).
- **Button-Free Aesthetic**: Clean frameless pill controls (`border-radius: 9999px`) with soft hover scaling (`transform: translateY(-1px)`).
- **Palette**: Forest Green (`#14382B`), Hunter Green (`#1E4D3B`), Accent Green (`#2A6B53`), Soft Base (`#E8F2EE`), Alert Crimson (`#8B2020`).
- **Zero Emoji Bloat**: Clean, professional UI text without emoji bloat.

---

## Pre-Seeded Demo Login Credentials

You can log in using either the **Work Email** or the **Employee Code** on the `/login` page:

### 1. HR Admin Accounts (`admin_hr` Role)
| Work Email | Employee Code | Password | Name & Job Title |
| :--- | :--- | :--- | :--- |
| `hr@company.com` | `HR_LEAD_01` | `admin123` | Sarah Jenkins (*Head of Human Resources*) |
| `hr_ops@company.com` | `HR_OPS_02` | `admin123` | Michael Vance (*HR Operations Specialist*) |

### 2. Standard Employee Accounts (`employee` Role)
| Work Email | Employee Code | Password | Name & Job Title | Department |
| :--- | :--- | :--- | :--- | :--- |
| `employee@company.com` | `EMP_001` | `emp123` | Alex Rivers (*Lead Software Engineer*) | Engineering |
| `david.dev@company.com` | `EMP_ENG_02` | `emp123` | David Chen (*Backend Systems Developer*) | Engineering |
| `elena.ux@company.com` | `EMP_UX_03` | `emp123` | Elena Rostova (*Senior UX Designer*) | Product & UX |
| `marcus.mkt@company.com` | `EMP_MKT_04` | `emp123` | Marcus Thorne (*Growth Marketing Manager*) | Marketing |
| `sophia.fin@company.com` | `EMP_FIN_05` | `emp123` | Sophia Alvarez (*Financial Analyst*) | Finance & Legal |

---

## CLI Database Management Commands

The project includes Makefile shortcuts and CLI scripts in [`scripts/`](scripts/):

```bash
# Seed basic admin & employee accounts
make seed-db            # or python -m scripts.seed_db

# Populate multi-department demo dataset with 8+ employees, attendance logs, and leave requests
make populate-db        # or python -m scripts.populate_sample_data

# Create or promote an HR Admin
make create-admin EMAIL=admin@company.com PASS=admin123

# Create a standard employee account
make create-user EMAIL=dev@company.com PASS=pass123 ROLE=employee

# Re-create all database schemas cleanly and re-seed
make reset-db           # or python -m scripts.reset_db
```

---

## Running the Application

### Using `make` (Linux / macOS)

```bash
# Start server on default port 8000
make run

# Start server on custom port (e.g. 8001)
make run-port PORT=8001

# Run full Pytest suite
make test
```

### Using `uvicorn` (Cross-Platform)

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## Testing & Quality Assurance

The codebase includes an extensive Pytest automated test suite covering database models, service layers, boundary conditions, and adversarial scenarios.

```bash
# Run the complete test suite
pytest -v
```

### Test Suite Breakdown (`50 Automated Tests`)

| Test File | Focus | Test Count | Description |
| :--- | :--- | :---: | :--- |
| [`tests/test_database.py`](tests/test_database.py) | Persistence & Models | 2 | Table creation, relationships, cascading & CRUD operations |
| [`tests/test_schema_sql.py`](tests/test_schema_sql.py) | Schema Verification | 6 | Raw SQL DDL structure, primary keys, foreign keys, & indexes |
| [`tests/test_logic_layer.py`](tests/test_logic_layer.py) | Domain Business Logic | 10 | Auth, RBAC enforcement, SEC-13 guards, overlap checks, sync |
| [`tests/test_adversarial_qa.py`](tests/test_adversarial_qa.py) | Business Rule Integrity | 14 | Adversarial testing against rules `LEAVE-01..09`, `ATT-01..08`, `SEC-01..13` |
| [`tests/test_edge_cases.py`](tests/test_edge_cases.py) | Boundary & Edge Cases | 18 | Zero duration shifts, approved leave guards, leap years, negative net pay |

---

## Documentation Hub

Explore the in-depth documentation in the [`docs/`](docs/) directory:

- [**Architecture Guide**](docs/architecture.md) — Multi-tier design, layer decoupling, security architecture, and styling rules.
- [**Database Design**](docs/database-design.md) — Schema definitions, indexes, design rationales, and constraints.
- [**Entity Relationship Diagram**](docs/er-diagram.md) — Relational model mapping & foreign key constraints.
- [**Permission & RBAC Matrix**](docs/permission-matrix.md) — Resource access rules and identity-trust guarantees.
- [**Workflows & Business Rules**](docs/workflows.md) — Leave lifecycle, attendance auto-sync, and payroll calculations.
- [**Edge Case & Boundary Decisions**](docs/edge_case_decisions.md) — Documented edge-case solutions and rationale.
- [**Testing & QA Guide**](docs/testing_guide.md) — Test architecture, fixtures, and verification inventory.

---
