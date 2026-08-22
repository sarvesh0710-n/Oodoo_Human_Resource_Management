# Dayflow HRMS — Permission Matrix

Two roles, stored on `USER.role`: **Employee** and **Admin/HR**.

Enforcement happens in the FastAPI **service layer**, on every request —
not in the frontend, and not only via a shared query helper that could be
bypassed. Every endpoint handler must:
1. Decode the JWT to get `user_id` and `role`.
2. For Employee-role requests touching a specific resource, resolve the
   resource's `employee_id` and compare it against the authenticated
   user's own `EMPLOYEE.id` — never trust an `employee_id` passed in the
   request body/query string.
3. Reject with 403 if the check fails, before any data is read or written.

## EMPLOYEE table

| Action | Employee | Admin/HR |
|---|---|---|
| Read own record | Yes | Yes |
| Read other employees' records | No | Yes |
| Edit own limited fields (phone, address, profile picture) | Yes | Yes |
| Edit all fields (department, job, manager) | No | Yes |
| Create employee | No | Yes |
| Delete employee | No | No (deactivate via USER.is_active instead) |

## ATTENDANCE table

| Action | Employee | Admin/HR |
|---|---|---|
| View own attendance | Yes | Yes |
| View all employees' attendance | No | Yes |
| Check in / check out (own) | Yes | Yes |
| Check in / check out (other employee) | No | No |
| Edit past attendance records | No | Yes |

## LEAVE_REQUEST table

| Action | Employee | Admin/HR |
|---|---|---|
| Submit leave request (own) | Yes | Yes |
| View own leave requests | Yes | Yes |
| View all leave requests | No | Yes |
| Approve / reject leave | No | Yes |
| Add review comment | No | Yes |
| Edit own pending request | Yes | Yes |
| Edit/cancel after approval | No | Yes |

## SALARY_STRUCTURE table

| Action | Employee | Admin/HR |
|---|---|---|
| View own salary structure | Yes (read-only) | Yes |
| View all salary structures | No | Yes |
| Create / edit salary structure | No | Yes |
| Delete salary structure | No | No (close via effective_to instead) |

## PAYSLIP table

| Action | Employee | Admin/HR |
|---|---|---|
| View own payslips | Yes (read-only) | Yes |
| View all payslips | No | Yes |
| Generate payslip | No | Yes |
| Edit/delete payslip | No | No (immutable once generated) |

Even Admin/HR should not edit/delete a generated payslip — regenerate via
a corrected salary structure if a mistake is found, to preserve the
historical-accuracy guarantee.

## DEPARTMENT table

| Action | Employee | Admin/HR |
|---|---|---|
| View | Yes | Yes |
| Create / edit / delete | No | Yes |

## AUDIT_LOG table

| Action | Employee | Admin/HR |
|---|---|---|
| View | No | Yes |
| Write | (system-generated only, never direct user write) | (system-generated only) |

## Implementation pattern (FastAPI)

A shared dependency (e.g. `get_current_user`) decodes the JWT and injects
the authenticated user into every protected route. A second layer —
`require_role(...)` or an ownership-check helper — is called inside each
route/service function that touches employee-scoped data, so the check
can't be skipped by forgetting to wire up a single global middleware.

## Security testing checklist (maps to test_security.py)

- Employee cannot read another employee's `EMPLOYEE` record by ID.
- Employee cannot read another employee's attendance/leave/payslip rows,
  including by manipulating the `employee_id` query param directly.
- Employee's JWT cannot be used to call salary_structure or payslip
  write/delete endpoints at all, regardless of ownership.
- Employee cannot call the leave-approval endpoint for their own or
  anyone's request.
- Admin/HR actions succeed against any employee's records.
- Requests with no token, an expired token, or a token for a deactivated
  user are rejected on every protected route.
