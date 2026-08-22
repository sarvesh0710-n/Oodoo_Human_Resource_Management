# Dayflow HRMS — Test Cases

Written for `pytest` + FastAPI's `TestClient` (or `httpx.AsyncClient`).
Every "Blocked" case must be tested by actually calling the endpoint with
a real (wrong-role or wrong-owner) JWT — not just checking the frontend —
since the point is proving server-side enforcement.

## test_attendance.py

| ID | Case | Expected result |
|---|---|---|
| ATT-01 | Employee checks in for the first time today | 201, row created with check_in set, check_out empty |
| ATT-02 | Employee checks in twice same day without checking out | 400, second check-in rejected |
| ATT-03 | Employee checks out without a prior check-in | 400, rejected |
| ATT-04 | Employee checks out after checking in | 200, check_out set, status computed as Present |
| ATT-05 | Query attendance status for a day with no record and no approved leave | Status = Absent |
| ATT-06 | Employee has an approved leave covering a given date | Attendance for that date = Leave (synced by approval) |
| ATT-07 | Admin/HR views another employee's attendance | 200, allowed |
| ATT-08 | Employee requests another employee's attendance via `employee_id` query param | 403, blocked regardless of param value |

## test_leave.py

| ID | Case | Expected result |
|---|---|---|
| LEAVE-01 | Employee submits leave with start_date after end_date | 400, validation error |
| LEAVE-02 | Employee submits leave overlapping an existing pending/approved request | 400, blocked |
| LEAVE-03 | Employee submits a valid leave request | 201, status = Pending |
| LEAVE-04 | Admin/HR approves a pending leave request | 200, status → Approved, reviewed_by/reviewed_at set |
| LEAVE-05 | Admin/HR rejects a leave request with a comment | 200, status → Rejected, comment stored |
| LEAVE-06 | Employee calls the approve/reject endpoint (own or anyone's request) | 403, blocked — no such permission for Employee role |
| LEAVE-07 | Leave approval triggers attendance sync | Attendance rows created/updated for each date in range with status Leave |
| LEAVE-08 | Employee edits a pending (not yet approved) leave request | 200, allowed |
| LEAVE-09 | Employee attempts to edit an already-approved leave request | 403, blocked |

## test_security.py

| ID | Case | Expected result |
|---|---|---|
| SEC-01 | Employee reads own EMPLOYEE record | 200 |
| SEC-02 | Employee reads another employee's EMPLOYEE record by ID | 403 |
| SEC-03 | Employee reads own SALARY_STRUCTURE | 200, read-only |
| SEC-04 | Employee attempts to write to SALARY_STRUCTURE (own or others') | 403 |
| SEC-05 | Employee attempts to create/delete a PAYSLIP | 403 |
| SEC-06 | Employee reads another employee's payslip by ID | 403 |
| SEC-07 | Admin/HR reads/writes any employee's salary structure | 200 |
| SEC-08 | Admin/HR generates a payslip for an employee | 201, snapshot fields match the active salary structure at generation time |
| SEC-09 | Two overlapping active SALARY_STRUCTURE rows for the same employee (effective_to = null on both) | Blocked — creating a new one auto-closes the previous |
| SEC-10 | Duplicate payslip for same employee/month/year | 409/400, blocked by unique constraint |
| SEC-11 | Request with no JWT / expired JWT / deactivated user's JWT | 401 on every protected route |
| SEC-12 | Employee calls leave-approval endpoint | 403, blocked regardless of UI state |
| SEC-13 | Request payload includes an `employee_id` different from the token's owner (Employee role) | 403 — server derives identity from token, never trusts the payload |

## Coverage notes

- SEC-04 / SEC-05 / SEC-06 / SEC-13 are the most judge-relevant tests:
  they prove salary and payslip data cannot leak to the wrong employee
  even via direct API manipulation, satisfying the "frontend hiding a
  button is not authorization" requirement explicitly.
- Attendance and leave tests should run against a seeded test database
  (pytest fixture) with at least two employee users and one admin user,
  so cross-employee access attempts have a real target to fail against.
