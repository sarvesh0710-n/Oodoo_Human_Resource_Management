# Dayflow HRMS — Permission & RBAC Matrix

This document defines the Role-Based Access Control (RBAC) rules, endpoint access privileges, identity-trust assertions, and `SEC-13` peer-approval rules enforced by Dayflow HRMS.

---

## 👥 Role Specifications

Dayflow HRMS standardizes strictly on **two user roles** stored on `User.role`:

1. **`employee`**: Regular staff member.
2. **`admin_hr`**: Combined HR Staff and System Administrator role.

> [!IMPORTANT]
> - There is **no third role** (no separate `admin` role).
> - All administrative actions (leave approval, salary configuration, payslip generation) are performed by `admin_hr`.

---

## 🔐 Resource Access Permission Table

| Resource | Action | Employee | Admin/HR | Enforcement Code |
| :--- | :--- | :---: | :---: | :--- |
| **User & Profile** | Read Own Profile | `ALLOW` | `ALLOW` | `app/services/employee_service.py` |
| | Read Other Employee Profile | `DENY (403)` | `ALLOW` | `app/services/employee_service.py` |
| | Create New Employee | `DENY (403)` | `ALLOW` | `app/api/employees.py` |
| | Edit Own Limited Fields (phone, address) | `ALLOW` | `ALLOW` | `app/services/employee_service.py` |
| | Edit Admin Fields (job, department, manager) | `DENY (403)` | `ALLOW` | `app/services/employee_service.py` |
| **Attendance** | Check-In / Check-Out (Own) | `ALLOW` | `ALLOW` | `app/services/attendance_service.py` |
| | Check-In / Check-Out (Other) | `DENY (403)` | `DENY (403)` | `app/services/attendance_service.py` |
| | View Own Attendance History | `ALLOW` | `ALLOW` | `app/services/attendance_service.py` |
| | View Other Employee Attendance | `DENY (403)` | `ALLOW` | `app/services/attendance_service.py` |
| **Leave Request** | Submit Leave Request (Own) | `ALLOW` | `ALLOW` | `app/services/leave_service.py` |
| | Edit Own Pending Request | `ALLOW` | `ALLOW` | `app/services/leave_service.py` |
| | Edit Approved/Rejected Request | `DENY (403)` | `DENY (403)` | `app/services/leave_service.py` |
| | Approve / Reject Leave Request (Peer) | `DENY (403)` | `ALLOW` | `app/services/leave_service.py` |
| | Approve / Reject Own Leave Request | `DENY (403)` | `DENY (403)` | `app/services/guards.py (SEC-13)` |
| **Salary Structure** | View Own Salary Structure | `ALLOW` | `ALLOW` | `app/services/payroll_service.py` |
| | View Other Employee Salary Structure | `DENY (403)` | `ALLOW` | `app/services/payroll_service.py` |
| | Create / Edit Salary Structure (Peer) | `DENY (403)` | `ALLOW` | `app/services/payroll_service.py` |
| | Create / Edit Own Salary Structure | `DENY (403)` | `DENY (403)` | `app/services/guards.py (SEC-13)` |
| **Payslip** | View Own Payslip Statement | `ALLOW` | `ALLOW` | `app/services/payroll_service.py` |
| | View Other Employee Payslip Statement | `DENY (403)` | `ALLOW` | `app/services/payroll_service.py` |
| | Generate Payslip (Peer) | `DENY (403)` | `ALLOW` | `app/services/payroll_service.py` |
| | Generate Own Payslip | `DENY (403)` | `DENY (403)` | `app/services/guards.py (SEC-13)` |
| **Department** | View Departments List | `ALLOW` | `ALLOW` | `app/api/departments.py` |
| | Create / Edit Department | `DENY (403)` | `ALLOW` | `app/api/departments.py` |

---

## 🛡️ Identity-Trust Verification Matrix

For every API endpoint taking an `employee_id` in request body, query, or path parameters, the server enforces strict identity verification:

```text
[ Client Request ]
       │
       ▼
[ JWT Authentication (deps.get_current_user) ] ──► Extract authenticated user_id & role
       │
       ├──► Role == "employee":
       │        Server ignores payload employee_id and uses authenticated Employee.id.
       │        If client explicitly passes employee_id != own Employee.id ──► Raise 403 Forbidden.
       │
       └──► Role == "admin_hr":
                Server verifies target Employee existence (Raise 404 if missing).
                Server calls assert_not_self_action(db, current_user, target_employee_id).
                If target_employee_id == own Employee.id ──► Raise 403 Forbidden (SEC-13).
                Else ──► Process Request.
```

### Endpoint Identity Audit

| Endpoint | HTTP Method | Identity Resolution | Protection Mechanism |
| :--- | :--- | :--- | :--- |
| `/api/attendance` | `GET` | Derived from JWT for `employee` | If `employee_id` param passed $\ne$ token owner, raises 403 |
| `/api/attendance/check-in` | `POST` | Derived from JWT | Identity locked to token owner `current_user.id` |
| `/api/attendance/check-out` | `POST` | Derived from JWT | Identity locked to token owner `current_user.id` |
| `/api/leave/requests` | `POST` | Derived from JWT | `employee_id` resolved from `current_user.id` |
| `/api/leave/requests` | `GET` | Derived from JWT for `employee` | Rejects cross-employee query params with 403 |
| `/api/leave/requests/{id}/review` | `PATCH` | `admin_hr` role + Peer check | Rejects `employee` role with 403; rejects self-action with 403 |
| `/api/payroll/structures` | `POST` | `admin_hr` role + Peer check | Rejects `employee` role with 403; rejects self-action with 403 |
| `/api/payroll/payslips` | `POST` | `admin_hr` role + Peer check | Rejects `employee` role with 403; rejects self-action with 403 |

---

## 🤝 Self-Action Guard (`SEC-13`) Peer Approval Model

To prevent administrative self-enrichment or conflict of interest:

1. **Leave Approval**: An `admin_hr` staff member cannot approve or reject their own leave request. A peer `admin_hr` user must perform the review.
2. **Salary Structure Setup**: An `admin_hr` staff member cannot configure their own base pay, allowances, or deductions. A peer `admin_hr` user must set up the structure.
3. **Payslip Generation**: An `admin_hr` staff member cannot issue their own monthly payslip statement. A peer `admin_hr` user must trigger generation.
