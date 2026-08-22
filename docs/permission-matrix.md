# Dayflow HRMS — Test Cases

Maps to `tests/test_attendance.py`, `tests/test_leave.py`,
`tests/test_security.py`. Written to be implemented with Odoo's
`TransactionCase`.

## test_attendance.py

| ID | Case | Expected result |
|---|---|---|
| ATT-01 | Employee checks in for the first time today | `hr.attendance` row created with check_in set, check_out empty |
| ATT-02 | Employee checks in twice on the same day without checking out | Second check-in blocked / raises validation error |
| ATT-03 | Employee checks out without a prior check-in | Blocked / raises validation error |
| ATT-04 | Employee checks out after checking in | check_out set on the same row, record now "Present" |
| ATT-05 | Query attendance status for a day with no record and no approved leave | Derived status = Absent |
| ATT-06 | Employee has an approved leave covering a given date | Attendance for that date reflects "Leave" (synced by leave approval) |
| ATT-07 | HR Officer views another employee's attendance | Allowed, full read access |
| ATT-08 | Employee views another employee's attendance via API/direct ID | Blocked by record rule |

## test_leave.py

| ID | Case | Expected result |
|---|---|---|
| LEAVE-01 | Employee submits leave with start_date after end_date | Validation error, rejected |
| LEAVE-02 | Employee submits leave overlapping an existing pending/approved request | Blocked / validation error |
| LEAVE-03 | Employee submits a valid leave request | Row created with state = draft/confirm (pending) |
| LEAVE-04 | HR Officer approves a pending leave request | state → validate; reviewed_by/approver and timestamp recorded |
| LEAVE-05 | HR Officer rejects a leave request with a comment | state → refuse; comment stored |
| LEAVE-06 | Employee attempts to approve their own leave request | Blocked — Employee group has no write access to state field / approval action |
| LEAVE-07 | Leave approval triggers attendance sync | hr.attendance rows created/updated for each date in range with Leave status |
| LEAVE-08 | Employee edits a pending (not yet approved) leave request | Allowed |
| LEAVE-09 | Employee attempts to edit an already-approved leave request | Blocked |

## test_security.py

| ID | Case | Expected result |
|---|---|---|
| SEC-01 | Employee reads own `hr.employee` record | Allowed |
| SEC-02 | Employee reads another employee's `hr.employee` record by ID | Blocked by record rule |
| SEC-03 | Employee reads own `hrms.salary.structure` | Allowed, read-only |
| SEC-04 | Employee attempts to write to `hrms.salary.structure` (own or others') | Blocked at access-rights level |
| SEC-05 | Employee attempts to create/delete a `hrms.payslip` | Blocked |
| SEC-06 | Employee reads another employee's payslip by direct ID/browse | Blocked by record rule |
| SEC-07 | HR Officer reads/writes any employee's salary structure | Allowed |
| SEC-08 | HR Officer generates a payslip for an employee | Allowed, snapshot fields match the active salary structure at generation time |
| SEC-09 | Two overlapping active `hrms.salary.structure` rows for the same employee (effective_to = null on both) | Blocked — creating a new one auto-closes the previous |
| SEC-10 | Duplicate payslip for same employee/month/year | Blocked by unique SQL constraint |
| SEC-11 | User with no Dayflow group assigned accesses any Dayflow menu | Blocked / menu not visible and action denied server-side |
| SEC-12 | Employee attempts to approve/reject any leave request | Blocked — no access to the approval action regardless of UI state |

## Coverage notes

- Every "Blocked" case must be tested by attempting the ORM call directly
  in the test (not just checking the UI), since the whole point is
  proving backend enforcement, not UI hiding.
- SEC-04/SEC-05/SEC-06 are the most judge-relevant tests: they prove
  salary and payslip data cannot leak to the wrong employee even via
  direct manipulation.
