# Dayflow HRMS — Modular Documentation Hub

Welcome to the official documentation for **Dayflow HRMS** — a modern, human-centric B2B Human Resource Management System built with **FastAPI**, **SQLAlchemy 2.0**, **Alembic**, and **Jinja2 Templates**.

---

## 📚 Documentation Index

| Module | Description | File Link |
| :--- | :--- | :--- |
| **System Architecture** | Technical stack, layer separation, FastAPI routers, JWT authentication, and dependency injection pattern. | [`architecture.md`](./architecture.md) |
| **Database Design** | Entity-Relationship (ER) design, schema definitions for all 9 tables, indexes, and PostgreSQL/SQLite dual engine setup. | [`database-design.md`](./database-design.md) |
| **Permission & RBAC Matrix** | Two-role access control (`employee` vs `admin_hr`), identity-trust rules, and `SEC-13` self-action peer approval guard. | [`permission-matrix.md`](./permission-matrix.md) |
| **Workflows & Business Rules** | Rule inventory (`LEAVE-01..09`, `ATT-01..08`, `SEC-01..13`), leave approval state machine, attendance auto-sync, and payroll calculation. | [`workflows.md`](./workflows.md) |
| **Edge Case & Boundary Decisions** | Comprehensive record of 17 explicit design decisions, boundary handling, and security guarantees. | [`edge_case_decisions.md`](./edge_case_decisions.md) |
| **Testing & QA Guide** | Pytest test suite architecture, fixture reference, 49 automated test cases, and verification commands. | [`testing_guide.md`](./testing_guide.md) |

---

## 📂 Project Structure Map

```text
Oodoo_Human_Resource_Management/
├── main.py                    # FastAPI Application Entrypoint & Middleware Setup
├── Makefile                   # Development Tasks & Port Management (make run, make test)
├── pytest.ini                 # Pytest Configuration
├── requirements.txt           # Python Dependencies
├── .env.example               # Environment Variable Template
│
├── app/                       # Core Application Package
│   ├── api/                   # REST API Endpoints (JSON)
│   │   ├── auth.py            # Authentication & JWT Endpoints (/api/auth)
│   │   ├── employees.py       # Employee Management (/api/employees)
│   │   ├── departments.py     # Department Operations (/api/departments)
│   │   ├── attendance.py      # Shift Logging & History (/api/attendance)
│   │   ├── leave.py           # Time-Off & Approval Queue (/api/leave)
│   │   └── payroll.py         # Salary Structures & Payslips (/api/payroll)
│   │
│   ├── core/                  # System Foundations
│   │   ├── config.py          # Application Settings & Env Loading
│   │   ├── database.py        # SQLAlchemy Engine, SessionLocal & Base
│   │   ├── security.py        # Password Hashing & JWT Token Encoding/Decoding
│   │   └── deps.py            # FastAPI Dependencies (get_db, get_current_user, require_role)
│   │
│   ├── models/                # SQLAlchemy ORM Data Models
│   │   ├── user.py            # User Auth & Credentials
│   │   ├── employee.py        # Employee Personal & Job Details
│   │   ├── department.py      # Department Hierarchy
│   │   ├── attendance.py      # Attendance Log Records
│   │   ├── leave.py           # Leave Types & Requests
│   │   ├── payroll.py         # Salary Structure & Monthly Payslips
│   │   └── audit_log.py       # System Action Audit Trail
│   │
│   ├── schemas/               # Pydantic Request & Response Schemas
│   │   └── __init__.py        # Input Validation & Output Serialization
│   │
│   ├── services/              # Pure Business & Domain Logic
│   │   ├── auth_service.py        # User Authentication Logic
│   │   ├── employee_service.py    # Employee Operations
│   │   ├── attendance_service.py  # Check-In/Out & Hours Calculation
│   │   ├── leave_service.py       # Leave Overlap & Attendance Sync
│   │   ├── payroll_service.py     # Salary Structures & Payslip Snapshotting
│   │   ├── audit_service.py       # System Event Logging
│   │   └── guards.py              # SEC-13 Self-Action Guard Assertions
│   │
│   ├── static/                # Static Web Assets
│   │   └── style.css          # Organic Windows Green Design System (Zero Gradients)
│   │
│   ├── templates/             # Jinja2 HTML Views (12 Pages)
│   │   ├── base.html          # Main Application Layout & Responsive Drawer
│   │   ├── login.html         # Sign-In View
│   │   ├── dashboard.html     # Employee Overview & Shift Clock
│   │   ├── admin_dashboard.html # HR Management Snapshot
│   │   ├── attendance.html    # Monthly Calendar & Detailed Logs
│   │   ├── leave.html         # Time-Off Quotas & Custom Green DatePicker
│   │   ├── leave_approvals.html # HR Approval Queue
│   │   ├── payroll.html       # Employee Payslips & Print Statement
│   │   ├── admin_payroll.html # HR Salary Setup & Payslip Generator
│   │   ├── employees.html     # Filterable Directory & Onboarding Modal
│   │   ├── departments.html   # Department Management
│   │   └── profile.html       # Employee Profile Card
│   │
│   └── web/                   # HTML Template Routes
│       └── views.py           # Page Rendering & Role Redirection
│
├── docs/                      # Technical Documentation Hub
│   ├── README.md              # Documentation Index & Map (This File)
│   ├── architecture.md        # Technical System Architecture
│   ├── database-design.md     # ER Model & Database Schema
│   ├── permission-matrix.md   # RBAC & Identity-Trust Matrix
│   ├── workflows.md           # Business Workflows & Rule Inventory
│   ├── edge_case_decisions.md # Boundary Handling & Explicit Decisions
│   └── testing_guide.md       # Pytest Suite Architecture & Execution
│
└── tests/                     # Automated Test Suites
    ├── test_database.py       # Database CRUD & Relationship Tests
    ├── test_schema_sql.py     # SQL DDL Schema Validation
    ├── test_logic_layer.py    # Core Service Logic & RBAC Tests
    ├── test_adversarial_qa.py # Adversarial Business Rule Validation
    └── test_edge_cases.py     # Boundary & Edge-Case Test Suite
```

---

## ⚡ Quick Start Commands

```bash
# 1. Install Dependencies
make install

# 2. Run Application Server (Port 8000)
make run

# 3. Run Application Server on Custom Port (e.g. 8001)
make run-port PORT=8001

# 4. Execute Full Automated Test Suite (49 Tests)
make test
```
