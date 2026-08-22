# Dayflow HRMS — Modern Human Resource Management System

[![Python Version](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00.svg?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Alembic](https://img.shields.io/badge/Alembic-Migrations-red.svg)](https://alembic.sqlalchemy.org/)
[![Database](https://img.shields.io/badge/Database-PostgreSQL%20%7C%20SQLite-336791.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Auth](https://img.shields.io/badge/Auth-JWT%20%2B%20HttpOnly%20Cookies-000000.svg?logo=jsonwebtokens&logoColor=white)](https://jwt.io/)
[![Design](https://img.shields.io/badge/Design-Organic%20Windows%20Green-1E4D3B.svg)](#-ui-design-system)
[![Tests](https://img.shields.io/badge/Tests-49%20Passing-brightgreen.svg?logo=pytest&logoColor=white)](./docs/testing_guide.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Dayflow HRMS** is an enterprise-grade, human-centric Human Resource Management System built with **FastAPI**, **SQLAlchemy 2.0**, **Alembic**, and **Jinja2 Server-Side Rendered Templates**. It provides a robust, production-ready solution to digitize all core HR operations — employee lifecycle management, department hierarchies, attendance logging, leave request workflows, salary structuring, immutable payslip generation, and comprehensive audit logging.

The system is architected with a strict separation of concerns, offering both **interactive server-rendered web portals** and a **high-performance RESTful API**, secured by JWT tokens in HttpOnly cookies, granular Role-Based Access Control (RBAC), and server-side self-action peer guards.

---

## 📑 Table of Contents

- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Technology Stack](#-technology-stack)
- [Database Schema & ERD](#-database-schema--erd)
- [Role-Based Access Control & Security](#-role-based-access-control--security)
- [Project Directory Structure](#-project-directory-structure)
- [Getting Started & Installation](#-getting-started--installation)
- [Running the Application](#-running-the-application)
- [CLI Database Management Scripts](#-cli-database-management-scripts)
- [API Documentation](#-api-documentation)
- [Testing & Quality Assurance](#-testing--quality-assurance)
- [Documentation Hub](#-documentation-hub)
- [License](#-license)

---

## 🌟 Key Features

### 1. 🔐 Enterprise Authentication & Session Security
- **OAuth2 JWT Token Authentication**: Encrypted `HS256` tokens stored in tamper-proof, secure `HttpOnly` cookies.
- **Fail-Fast Security Setup**: Enforces explicit `SECRET_KEY` configuration on startup.
- **CSRF & XSS Protection**: Strict cookie flags (`SameSite=Lax`), context-aware HTML escaping, and request verification.
- **Password Security**: Salted `bcrypt` hashing with `passlib`.

### 2. 👤 Employee Directory & Organization Hierarchy
- **Complete Employee Profiles**: First/last name, job title, contact information, address, joining date, and avatar.
- **1:1 Auth Isolation**: Separation between authentication identity (`User`) and organizational profile (`Employee`).
- **Reporting Line Hierarchy**: Built-in self-referential manager linkage (`Employee.manager_id`) supporting multi-tiered organizational structures.

### 3. ⏱️ Attendance & Shift Tracking
- **One-Click Clock-In / Clock-Out**: Streamlined daily shift tracking with timestamp validation (`check_out > check_in`).
- **Zero-Duration Rejection**: Prevents duplicate or instantaneous check-out anomalies.
- **Dynamic Attendance Status**: Computes and derives `Present`, `Absent`, `Half-day`, and `Leave` states.
- **Monthly Attendance Log**: Visual grid calendar and downloadable/printable log history.

### 4. 📅 Time-Off & Leave Management
- **Leave Types & Allowances**: Pre-configured categories (Paid Time Off, Medical/Sick Leave, Unpaid Leave).
- **Date Range Overlap Prevention**: Strict server-side validation against overlapping leave windows (`start_date <= existing.end_date AND end_date >= existing.start_date`).
- **HR Review Workflow**: Review queue for HR Administrators with approval/rejection comments and audit timestamps.
- **Atomic Attendance Synchronization**: Approving a leave request automatically creates or updates the employee's attendance records to `status='Leave'` across the entire requested date range.

### 5. 💰 Payroll & Compensation Engine
- **Salary Structures**: Time-bound compensation packages with `basic_salary`, `allowances`, `deductions`, `effective_from`, and `effective_to`.
- **Automatic Versioning**: Creating a new salary structure automatically closes out previous active structures.
- **Immutable Monthly Payslips**: Generates permanent point-in-time financial snapshots (`gross_salary`, `net_salary`) unaffected by future pay adjustments.
- **Financial Bounds**: Enforces positive values, non-negative net earnings, and an upper limit ceiling (`$10,000,000.00`).
- **Printable Statements**: Clean CSS print styling for individual monthly payslips.

### 6. 🏢 Department Management
- Normalized departments with descriptions and assigned department heads.
- Dynamic employee counts and department-wise employee filtering.

### 7. 🛡️ System Audit Trail & Self-Action Guards (`SEC-13`)
- **`SEC-13` Peer-Approval Guard**: Built-in safeguards (`assert_not_self_action`) preventing HR Administrators from approving their own leaves, setting their own salary structures, or generating their own payslips.
- **Audit Logging**: Captures sensitive mutations in `audit_logs` table with user identification, action type, target entity, and timestamp.

---

## 🏛️ System Architecture

Dayflow HRMS is built around a **Layered Domain Architecture Pattern**:

```text
               ┌─────────────────────────────────────────┐
               │         Client Browser / REST API       │
               └────────────────────┬────────────────────┘
                                    │
               ┌────────────────────▼────────────────────┐
               │    FastAPI Presentation Layer           │
               │   • Jinja2 HTML Views (app/web/views.py)│
               │   • JSON REST APIs    (app/api/*.py)    │
               └────────────────────┬────────────────────┘
                                    │
               ┌────────────────────▼────────────────────┐
               │    Security & Dependency Injection      │
               │   • JWT Cookie Auth (app/core/deps.py)  │
               │   • Role-Based Guard (require_role)     │
               └────────────────────┬────────────────────┘
                                    │
               ┌────────────────────▼────────────────────┐
               │    Domain Service Layer                 │
               │   • Attendance, Leave, Payroll Services │
               │   • SEC-13 Self-Action Guards           │
               │   • Audit Logging Dispatcher            │
               └────────────────────┬────────────────────┘
                                    │
               ┌────────────────────▼────────────────────┐
               │    Data Persistence (SQLAlchemy 2.0)    │
               │   • Declarative ORM Models (app/models/)│
               │   • PostgreSQL / SQLite Dual Support    │
               │   • Alembic Versioned Migrations        │
               └─────────────────────────────────────────┘
```

### 🎨 UI Design System

The web frontend uses a custom **Organic Windows Green** aesthetic ([`app/static/style.css`](app/static/style.css)):
- **Palette**: Forest Green (`#14382B`), Hunter Green (`#1E4D3B`), Accent Green (`#2A6B53`), Soft Base (`#E8F2EE`), Alert Crimson (`#8B2020`).
- **Zero Gradients**: Solid, crisp surfaces for high legibility and instant rendering performance.
- **Adaptive Layout**: Desktop sidebar navigation with mobile-friendly off-canvas drawer navigation.

---

## 💻 Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | **FastAPI** (Python 3.11 / 3.12+) | High-performance ASGI web framework & routing engine |
| **Web Presentation** | **Jinja2** + **Vanilla CSS/JS** | Lightweight, reactive Server-Side Rendered (SSR) UI |
| **ORM & Persistence** | **SQLAlchemy 2.0+** | Declarative data modeling, relationships, and queries |
| **Database Migrations**| **Alembic** | Reliable schema versioning and upgrade/downgrade paths |
| **Database Engines** | **PostgreSQL 15+** / **SQLite** | Production RDBMS with local zero-setup SQLite fallback |
| **Authentication** | **python-jose** + **passlib** (bcrypt)| Signed JWT tokens & salted password hashing |
| **Data Validation** | **Pydantic v2** | Request schema parsing and type validation |
| **Test Framework** | **Pytest** + **httpx** | 49 comprehensive unit, integration, and QA test cases |

---

## 📊 Database Schema & ERD

The database schema is defined in SQLAlchemy ORM models ([`app/models/`](app/models/)) with corresponding raw PostgreSQL DDL in [`database/schema.sql`](database/schema.sql).

### Entity Relationship Diagram

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

### Table Summary

| Table | Model | Description |
| :--- | :--- | :--- |
| `users` | [`User`](app/models/user.py) | Credentials, email, employee code, active status, role (`employee` / `admin_hr`) |
| `employees` | [`Employee`](app/models/employee.py) | 1:1 employee record, contact details, job title, department, and manager |
| `departments` | [`Department`](app/models/department.py) | Business units with name, description, and department manager |
| `attendance` | [`Attendance`](app/models/attendance.py) | Daily check-in/out timestamps, hours worked, and status (`Present`, `Leave`, etc.) |
| `leave_types` | [`LeaveType`](app/models/leave.py) | Leave policies (Paid, Sick, Unpaid) |
| `leave_requests` | [`LeaveRequest`](app/models/leave.py) | Employee leave submissions, dates, status (`Pending`, `Approved`, `Rejected`), and comments |
| `salary_structures` | [`SalaryStructure`](app/models/payroll.py) | Active and historical pay formulas with effective dates |
| `payslips` | [`Payslip`](app/models/payroll.py) | Immutable point-in-time monthly payroll statements |
| `audit_logs` | [`AuditLog`](app/models/audit_log.py) | System audit log of privileged operations and state changes |

---

## 👥 Role-Based Access Control & Security

Dayflow HRMS standardizes strictly on a **Two-Role Model**:
1. **`employee`**: Standard staff access (own profile, attendance clock, personal leave requests, personal payslips).
2. **`admin_hr`**: Elevated HR Administrator (company-wide employee directory, department setup, leave approvals, salary configuration, payslip generation).

### Permission Matrix

| Operation | Employee | Admin/HR | Security Guard |
| :--- | :---: | :---: | :--- |
| View Own Profile / Attendance / Leave / Payslips | ✅ | ✅ | Direct user token identity binding |
| Clock-In / Clock-Out (Own Record) | ✅ | ✅ | Cannot clock in for another user |
| Submit / Cancel Own Pending Leave Request | ✅ | ✅ | Locked once approved or rejected |
| View Company Directory & Other Profiles | ❌ (403) | ✅ | Role-restricted route |
| Create / Edit Employee Records | ❌ (403) | ✅ | Role-restricted route |
| Manage Departments & Assignments | ❌ (403) | ✅ | Role-restricted route |
| Approve / Reject Leave Requests (Peer) | ❌ (403) | ✅ | Role-restricted route |
| **Approve / Reject Own Leave Request** | ❌ (403) | ❌ (403) | **`SEC-13` Self-Action Guard Blocked** |
| Configure Salary Structure (Peer) | ❌ (403) | ✅ | Role-restricted route |
| **Configure Own Salary Structure** | ❌ (403) | ❌ (403) | **`SEC-13` Self-Action Guard Blocked** |
| Generate Payslips (Peer) | ❌ (403) | ✅ | Role-restricted route |
| **Generate Own Payslip** | ❌ (403) | ❌ (403) | **`SEC-13` Self-Action Guard Blocked** |

---

## 📁 Project Directory Structure

```text
Oodoo_Human_Resource_Management/
├── main.py                     # Application entrypoint & startup data seeder
├── requirements.txt            # Python package dependencies
├── .env.example                # Environment variable configuration template
├── .gitignore                  # Git tracking rules
├── pytest.ini                  # Pytest configuration
├── Makefile                    # Automation commands (Linux / macOS)
├── alembic.ini                 # Alembic configuration
│
├── alembic/                    # Database migration environment
│   └── versions/               # Versioned migration revision scripts
│
├── app/                        # Main Application Package
│   ├── api/                    # REST API Endpoints (JSON)
│   │   ├── auth.py             # Login, registration, token refresh (/api/auth)
│   │   ├── employees.py        # Employee management (/api/employees)
│   │   ├── departments.py      # Department operations (/api/departments)
│   │   ├── attendance.py       # Attendance tracking (/api/attendance)
│   │   ├── leave.py            # Leave request workflows (/api/leave)
│   │   └── payroll.py          # Salary structures & payslips (/api/payroll)
│   │
│   ├── core/                   # Core Configuration & Security
│   │   ├── database.py         # SQLAlchemy engine & session factory
│   │   ├── security.py         # Passlib hashing & JWT encoding/decoding
│   │   └── deps.py             # FastAPI dependency injection & RBAC guards
│   │
│   ├── models/                 # SQLAlchemy 2.0 Declarative Models
│   │   ├── user.py             # User authentication model
│   │   ├── employee.py         # Employee profile model
│   │   ├── department.py       # Department model
│   │   ├── attendance.py       # Shift attendance log model
│   │   ├── leave.py            # Leave type & request models
│   │   ├── payroll.py          # Salary structure & payslip models
│   │   └── audit_log.py        # System audit log model
│   │
│   ├── schemas/                # Pydantic Request & Response Schemas
│   │   └── __init__.py         # Type validation & serializers
│   │
│   ├── services/               # Business Logic & Guard Layer
│   │   ├── auth_service.py     # Authentication logic
│   │   ├── employee_service.py # Directory operations
│   │   ├── attendance_service.py # Shift & duration calculations
│   │   ├── leave_service.py    # Overlap validation & attendance sync
│   │   ├── payroll_service.py  # Compensation & payslip snapshotting
│   │   ├── audit_service.py    # System event recorder
│   │   └── guards.py           # SEC-13 Self-action peer guard
│   │
│   ├── static/                 # Static Assets
│   │   └── style.css           # Organic Windows Green design system
│   │
│   ├── templates/              # Jinja2 HTML Server-Rendered Views
│   │   ├── base.html           # Core layout, header, & responsive sidebar
│   │   ├── login.html          # Authentication login page
│   │   ├── dashboard.html      # Employee dashboard & shift clock
│   │   ├── admin_dashboard.html# HR Admin operations hub
│   │   ├── employees.html      # Employee directory & creation modal
│   │   ├── departments.html    # Department list & manager manager
│   │   ├── attendance.html     # Attendance grid & history table
│   │   ├── leave.html          # Leave request portal & status list
│   │   ├── leave_approvals.html# HR leave approval queue
│   │   ├── payroll.html        # Employee payslip statement view
│   │   ├── admin_payroll.html  # HR salary structuring & bulk generation
│   │   └── profile.html        # Personal profile editor
│   │
│   └── web/                    # Web UI Route Handlers
│       └── views.py            # SSR template view renderers
│
├── database/                   # Standalone Database DDL
│   └── schema.sql              # Raw PostgreSQL schema definition
│
├── docs/                       # Technical Documentation Hub
│   ├── README.md               # Documentation guide index
│   ├── architecture.md         # Detailed architectural design
│   ├── database-design.md      # Data model & schema decisions
│   ├── er-diagram.md           # Mermaid ER diagram specification
│   ├── permission-matrix.md    # RBAC security & endpoint access rules
│   ├── workflows.md            # Business rule inventory (LEAVE, ATT, SEC)
│   ├── edge_case_decisions.md  # 17 explicit boundary & edge-case decisions
│   └── testing_guide.md        # QA test suite breakdown
│
├── scripts/                    # Command-Line Management Utilities
│   ├── seed_db.py              # Seeds basic admin & employee accounts
│   ├── populate_sample_data.py # Populates multi-department demo database
│   ├── create_admin.py         # CLI utility to create an HR Admin
│   ├── create_user.py          # CLI utility to create standard employees
│   └── reset_db.py             # Complete database wipe & re-seed
│
└── tests/                      # Automated Test Suite (49 Tests)
    ├── test_database.py        # ORM model CRUD & relationship tests
    ├── test_schema_sql.py      # Schema DDL structure tests
    ├── test_logic_layer.py     # Service layer business logic & RBAC tests
    ├── test_adversarial_qa.py  # Adversarial validation against business rules
    ├── test_edge_cases.py      # Boundary handling & edge-case tests
    └── test_postgres_integration.py # Live PostgreSQL constraint tests
```

---

## 🚀 Getting Started & Installation

### Prerequisites
- **Python**: Version `3.11` or `3.12+`
- **PostgreSQL** *(Optional)*: Version 15+ (If omitted, the system seamlessly defaults to SQLite `dayflow.db`)

### 1. Clone the Repository
```bash
git clone https://github.com/sarvesh0710-n/Oodoo_Human_Resource_Management.git
cd Oodoo_Human_Resource_Management
```

### 2. Create and Activate a Virtual Environment

**On Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:

```bash
# On Linux / macOS
cp .env.example .env

# On Windows PowerShell
Copy-Item .env.example .env
```

Edit `.env` to configure your settings:
```ini
DATABASE_URL=sqlite:///dayflow.db
# Or for PostgreSQL:
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dayflow_hrms

SECRET_KEY=generate_a_secure_random_string_for_production
DAYFLOW_ENV=dev
```

### 5. Initialize the Database
Run migrations or populate sample data:
```bash
# Option A: Run Alembic migrations
alembic upgrade head

# Option B: Populate rich demo data (Multiple departments, employees, shifts, leaves)
python -m scripts.populate_sample_data
```

---

## 🖥️ Running the Application

### Using `uvicorn` (Cross-Platform)

```bash
# Start server on default port 8000
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Using `make` (Linux / macOS)

```bash
# Start server on port 8000
make run

# Start server on custom port (e.g. 8001)
make run-port PORT=8001
```

### 🌐 Accessing the Application

Open your browser and navigate to:
- **Web UI Portal**: [http://localhost:8000/login](http://localhost:8000/login)
- **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative ReDoc API Docs**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 🔑 Demo Credentials

| Role | Email | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **HR Administrator** | `hr@company.com` | `admin123` | Full HR Admin access across all modules |
| **Standard Employee**| `employee@company.com` | `emp123` | Personal profile, attendance, leave, payslips |

---

## 🛠️ CLI Database Management Scripts

The `scripts/` directory provides CLI tools for database administration:

```bash
# Seed initial demo admin & employee
python -m scripts.seed_db

# Populate full mock company dataset (5+ employees, attendance logs, leave history)
python -m scripts.populate_sample_data

# Create or promote an HR Admin
python -m scripts.create_admin --email admin@example.com --password YourSecurePassword

# Create a standard employee account
python -m scripts.create_user --email staff@example.com --password UserPassword --role employee

# Complete database reset & fresh re-seed
python -m scripts.reset_db
```

---

## 📖 API Documentation

FastAPI automatically generates interactive OpenAPI documentation:

- **Swagger UI**: [`http://localhost:8000/docs`](http://localhost:8000/docs)
- **ReDoc**: [`http://localhost:8000/redoc`](http://localhost:8000/redoc)

### Key REST Endpoints Overview

| Area | Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- | :---: |
| **Auth** | `POST` | `/api/auth/token` | Obtain JWT access token | No |
| | `POST` | `/api/auth/logout` | Clear session cookie | Yes |
| | `GET` | `/api/auth/me` | Fetch authenticated user details | Yes |
| **Employees**| `GET` | `/api/employees/` | List all employees | `admin_hr` |
| | `POST` | `/api/employees/` | Create new employee profile | `admin_hr` |
| | `GET` | `/api/employees/{id}` | Get employee profile details | Owner / `admin_hr` |
| | `PATCH`| `/api/employees/{id}` | Update employee profile fields | Owner / `admin_hr` |
| **Attendance**| `POST` | `/api/attendance/check-in` | Clock in for today's shift | Yes |
| | `POST` | `/api/attendance/check-out` | Clock out for today's shift | Yes |
| | `GET` | `/api/attendance/` | Query attendance logs (filtered) | Owner / `admin_hr` |
| **Leave** | `POST` | `/api/leave/` | Submit leave request | Yes |
| | `GET` | `/api/leave/` | List leave requests | Owner / `admin_hr` |
| | `PATCH`| `/api/leave/{id}/review` | Approve or reject leave request | `admin_hr` (Non-self) |
| **Payroll** | `POST` | `/api/payroll/salary-structure` | Create/update salary structure | `admin_hr` (Non-self) |
| | `POST` | `/api/payroll/generate-payslip` | Generate monthly payslip snapshot | `admin_hr` (Non-self) |
| | `GET` | `/api/payroll/payslips` | List historical payslips | Owner / `admin_hr` |
| **Departments**| `GET` | `/api/departments/` | List departments | Yes |
| | `POST` | `/api/departments/` | Create new department | `admin_hr` |

---

## 🧪 Testing & Quality Assurance

The codebase includes an extensive Pytest automated test suite covering database models, service layers, boundary conditions, and adversarial scenarios.

```bash
# Run the complete test suite
pytest -v

# Run specific test suites
pytest -v tests/test_logic_layer.py
pytest -v tests/test_adversarial_qa.py
pytest -v tests/test_edge_cases.py
```

### Test Suite Breakdown (`49 Automated Tests`)

| Test File | Focus | Test Count | Description |
| :--- | :--- | :---: | :--- |
| [`tests/test_database.py`](tests/test_database.py) | Persistence & Models | 2 | Table creation, relationships, cascading & CRUD operations |
| [`tests/test_schema_sql.py`](tests/test_schema_sql.py) | Schema Verification | 6 | Raw SQL DDL structure, primary keys, foreign keys, & indexes |
| [`tests/test_logic_layer.py`](tests/test_logic_layer.py) | Domain Business Logic | 10 | Auth, RBAC enforcement, SEC-13 guards, overlap checks, sync |
| [`tests/test_adversarial_qa.py`](tests/test_adversarial_qa.py) | Business Rule Integrity | 14 | Adversarial testing against rules `LEAVE-01..09`, `ATT-01..08`, `SEC-01..13` |
| [`tests/test_edge_cases.py`](tests/test_edge_cases.py) | Boundary & Edge Cases | 17 | Zero duration shifts, leap years, negative net pay, token expiry |

For full QA specifications, see the [Testing & QA Guide](docs/testing_guide.md).

---

## 📚 Documentation Hub

Explore the in-depth documentation in the [`docs/`](docs/) directory:

- 🏛️ [**Architecture Guide**](docs/architecture.md) — Multi-tier design, layer decoupling, security architecture, and styling rules.
- 🗄️ [**Database Design**](docs/database-design.md) — Schema definitions, indexes, design rationales, and constraints.
- 📊 [**Entity Relationship Diagram**](docs/er-diagram.md) — Visual Mermaid ERD and relational model mapping.
- 🔐 [**Permission & RBAC Matrix**](docs/permission-matrix.md) — Resource access rules and identity-trust guarantees.
- ⚙️ [**Workflows & Business Rules**](docs/workflows.md) — Leave lifecycle, attendance auto-sync, and payroll calculations.
- 🎯 [**Edge Case & Boundary Decisions**](docs/edge_case_decisions.md) — 17 documented edge-case solutions and rationale.
- 🧪 [**Testing & QA Guide**](docs/testing_guide.md) — Test architecture, fixtures, and verification inventory.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
