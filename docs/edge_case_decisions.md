# Dayflow HRMS — Edge-Case Architecture & Design Decisions

This document summarizes every explicit design decision made during the edge-case hardening pass for Dayflow HRMS, formatted for evaluation review.

---

## 📅 Leave Module Edge Cases

### 1. Single-Day Leave Requests (`start_date == end_date`)
- **Decision**: Allowed.
- **Rationale**: `start_date > end_date` validation check evaluates to `False` when `start_date == end_date`. A single-day leave (e.g., `2027-05-10` to `2027-05-10`) is a common business request and is explicitly supported.

### 2. Overlap Check Date Range Boundaries & Adjacency
- **Decision**: Leave date ranges `[start_date, end_date]` are strictly **inclusive** of both boundary dates.
- **Rationale**: A request from Dec 1 to Dec 5 includes Dec 5. Therefore, a subsequent request starting on Dec 5 (e.g. Dec 5 to Dec 8) overlaps on Dec 5 and is rejected with HTTP 400. Truly adjacent requests (e.g. Dec 1 to Dec 5 and Dec 6 to Dec 8) do NOT intersect and are allowed.

### 3. Editing a Pending Leave Request to Same Dates
- **Decision**: Supported without self-overlap false positives.
- **Rationale**: `update_pending_leave_request` queries overlapping requests filtering `LeaveRequest.id != leave_id`, ensuring a pending request being edited to the exact same dates is not flagged as overlapping itself.

### 4. Month/Year Rollover Attendance Auto-Sync
- **Decision**: Iterated via `timedelta(days=1)`.
- **Rationale**: Python's `datetime.date` arithmetic handles month and year rollovers (e.g., Dec 30, 2026 to Jan 2, 2027) seamlessly without manual calendar math.

### 5. Rejection vs Approval Attendance Sync
- **Decision**: Attendance auto-sync executes **only** when `data.status == "approved"`.
- **Rationale**: Rejecting a leave request (`status == "rejected"`) must not create or alter attendance records.

### 6. Concurrency / Rapid Succession Submissions
- **Decision**: Standard query-then-insert within SQLAlchemy transaction boundaries.
- **Rationale**: For this application's target scale, standard transactional checks suffice. For high-concurrency environments, database-level unique constraints or SELECT FOR UPDATE row locking can be enabled.

---

## ⏱️ Attendance Module Edge Cases

### 1. Midnight Boundary Check-In
- **Decision**: `date.today()` evaluates server local date.
- **Rationale**: The backend server timezone is the single authoritative source of date identity across all check-ins.

### 2. Zero-Duration Shift (`check_out == check_in`)
- **Decision**: Rejected with HTTP 400 Bad Request.
- **Rationale**: A check-out time equal to check-in time represents an invalid 0-second shift. `check_out` must be strictly after `check_in`.

### 3. Admin HR Querying Non-Existent `employee_id` Attendance
- **Decision**: Rejected with HTTP 404 Not Found.
- **Rationale**: Returning an empty list for a non-existent employee ID creates misleading ambiguity ("employee exists but has no attendance"). Raising 404 explicitly indicates the employee record does not exist.

---

## 💰 Payroll Module Edge Cases

### 1. Future `effective_from` Salary Structures
- **Decision**: Excluded from current or past payslip generation.
- **Rationale**: `generate_payslip` checks `SalaryStructure.effective_from <= period_end_date`. A structure with a future `effective_from` date (e.g. Oct 2026) will not be picked up for a prior payslip period (e.g. Aug 2026).

### 2. Payslip Requested Prior to Employee's First Salary Structure
- **Decision**: Rejected with HTTP 400 Bad Request.
- **Rationale**: Generating a payslip for a month/year prior to the employee's first active salary structure `effective_from` date returns `"No active salary structure found for period M/YYYY"`.

### 3. Zero-Value Allowances & Deductions (`$0.00`)
- **Decision**: Supported.
- **Rationale**: Decimal additions and subtractions with `Decimal("0.00")` calculate gross and net salaries correctly.

### 4. Deductions Exceeding Gross Salary (Negative Net Salary)
- **Decision**: Rejected with HTTP 400 Bad Request.
- **Rationale**: Deductions greater than basic salary plus allowances (`deductions > gross`) produce a negative net salary, which is invalid in business payroll operations and indicates misconfigured deductions.

### 5. Salary Structure for Non-Existent `employee_id`
- **Decision**: Rejected with HTTP 404 Not Found.
- **Rationale**: `create_salary_structure` checks target `Employee` existence first, preventing raw database foreign key constraint crashes.

---

## 🔐 RBAC & Auth Edge Cases

### 1. JWT for Deleted User Account
- **Decision**: Rejected with HTTP 401 Unauthorized.
- **Rationale**: `get_current_user` queries the database on every request. If the user ID no longer exists, HTTP 401 is raised cleanly.

### 2. Mid-Session Account Deactivation (`is_active = False`)
- **Decision**: Rejected on next request with HTTP 401 Unauthorized.
- **Rationale**: `get_current_user` validates `user.is_active` on every request, immediately revoking access if an account is deactivated after login.

### 3. Malformed Authorization Headers
- **Decision**: Rejected with HTTP 401 Unauthorized.
- **Rationale**: Missing `Bearer` prefix, empty tokens, non-integer `sub` claims, or garbage strings are caught in `get_current_user` and returned as HTTP 401 without unhandled exceptions.

### 4. Admin HR Without Linked Employee Record
- **Decision**: `assert_not_self_action` evaluates safely to `False` (no-op).
- **Rationale**: If an `admin_hr` User account does not have a linked `Employee` record, `emp` is `None`, so `emp.id == target_employee_id` evaluates safely without throwing an exception.
