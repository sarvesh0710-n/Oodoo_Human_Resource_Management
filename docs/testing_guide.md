# Dayflow HRMS — Testing & QA Guide

This document describes the test suite architecture, fixture setup, test inventory, and execution commands for **Dayflow HRMS**.

---

## 🧪 Test Suite Architecture

The automated test suite is built using **Pytest** and FastAPI's **`TestClient`**. Tests execute against an isolated **SQLite in-memory database** (`sqlite:///:memory:`) using standard SQLAlchemy transaction rollbacks.

```text
tests/
├── test_database.py       # Table metadata, relationships & model CRUD tests
├── test_schema_sql.py     # DDL table definition & schema validation tests
├── test_logic_layer.py    # Core service logic, RBAC, & self-action guard tests
├── test_adversarial_qa.py # Rule inventory adversarial validation (LEAVE-01..09, SEC-01..13)
└── test_edge_cases.py     # Boundary handling & 20 explicit edge-case decision tests
```

---

## 📋 Comprehensive Test Inventory (`49 Total Tests`)

### 1. Database & Schema Tests (`tests/test_database.py` & `test_schema_sql.py`)
- `test_tables_created`: Verifies all 9 core tables exist in metadata (`user`, `department`, `employee`, `attendance`, `leave_type`, `leave_request`, `salary_structure`, `payslip`, `audit_log`).
- `test_full_crud_and_relationships`: Verifies insertion, query, and relationship loading across all 9 models.
- `test_sql_schema_definitions`: Verifies primary keys, foreign keys, and indexes.

### 2. Service Logic & RBAC Tests (`tests/test_logic_layer.py`)
- `test_auth_success`: Validates successful user authentication.
- `test_auth_wrong_password`: Validates HTTP 401 on incorrect password.
- `test_auth_wrong_email`: Validates HTTP 401 on unknown email address.
- `test_auth_inactive_user`: Validates HTTP 401 on deactivated user account.
- `test_rbac_employee_blocked_from_admin_actions`: Confirms `employee` role receives HTTP 403 on admin-only endpoints.
- `test_self_action_guard_on_leave_review`: Confirms `admin_hr` self leave approval is blocked (HTTP 403) and peer approval succeeds.
- `test_self_action_guard_on_payroll`: Confirms `admin_hr` self salary setup and self payslip generation are blocked (HTTP 403).
- `test_leave_overlap_creation_and_editing`: Confirms overlapping leave requests are rejected on creation and edit.
- `test_payslip_duplicate_idempotency`: Confirms duplicate `(employee_id, month, year)` payslip returns HTTP 409 Conflict.
- `test_attendance_sync_on_leave_approval`: Confirms leave approval syncs attendance rows with `status='leave'`.

### 3. Adversarial QA Suite (`tests/test_adversarial_qa.py`)
- 14 adversarial test cases verifying strict compliance with rules `LEAVE-01` to `LEAVE-09`, `ATT-01` to `ATT-08`, and `SEC-01` to `SEC-13`.

### 4. Boundary & Edge-Case Suite (`tests/test_edge_cases.py`)
- `test_leave_single_day_request`: Single-day leave (`start_date == end_date`).
- `test_leave_overlap_boundary_adjacency`: Inclusive date range overlap vs adjacent non-overlapping ranges.
- `test_leave_edit_pending_same_dates`: Editing pending request to same dates without self-collision false positive.
- `test_leave_year_rollover_attendance_sync`: Month/year rollover (Dec 30 to Jan 2) attendance sync.
- `test_leave_leap_year_dates`: Leap year date inputs (Feb 29).
- `test_leave_rejection_does_not_touch_attendance`: Rejection does not create/update attendance.
- `test_attendance_zero_duration_shift_rejected`: Check-out equal to check-in (`zero-duration`) rejected with HTTP 400.
- `test_attendance_query_non_existent_employee_404`: Querying non-existent `employee_id` returns HTTP 404.
- `test_payroll_future_salary_structure_not_used_for_past_period`: Future `effective_from` structure excluded from prior payslips.
- `test_payroll_payslip_before_employee_first_structure_rejected`: Payslip period prior to first salary structure returns HTTP 400.
- `test_payroll_zero_allowances_deductions`: `$0.00` allowances/deductions processed cleanly.
- `test_payroll_negative_net_salary_rejected`: Deductions exceeding gross salary (`net < 0`) rejected with HTTP 400.
- `test_payroll_non_existent_employee_structure_rejected`: Non-existent `employee_id` returns HTTP 404.
- `test_auth_deleted_user_returns_401`: Token for deleted user returns HTTP 401.
- `test_auth_deactivated_mid_session_returns_401`: Token for user deactivated mid-session returns HTTP 401.
- `test_auth_malformed_authorization_header`: Missing `Bearer` prefix or garbage token returns HTTP 401.
- `test_self_action_guard_admin_no_employee_record_no_crash`: Admin HR without linked employee record no-ops safely.

---

## ⚡ Execution Commands

```bash
# Run full automated test suite
.venv/bin/pytest

# Run test suite with verbose output
.venv/bin/pytest -v

# Run specific test module
.venv/bin/pytest tests/test_edge_cases.py -v

# Run specific test function
.venv/bin/pytest tests/test_edge_cases.py -k test_payroll_negative_net_salary_rejected
```
