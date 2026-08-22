# Dayflow HRMS — Entity Relationship Diagram (ERD)

This document visualizes the complete entity relationship diagram for the **Dayflow HRMS** database.

---

## 📊 Visual ER Diagram

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
    string profile_picture
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

---

## 🗄️ Relational Model Overview

| Entity | Primary Key | Foreign Keys & References | Key Cardinality | Description |
| :--- | :--- | :--- | :--- | :--- |
| **`User`** | `id` (Auto-increment) | None | 1:1 with `Employee` | Authentication identity & role credentials (`employee` vs `admin_hr`). |
| **`Employee`** | `id` (Auto-increment) | `user_id` (Unique FK), `department_id` (FK), `manager_id` (Self-referential FK) | 1:N with `Attendance`, `LeaveRequest`, `SalaryStructure`, `Payslip` | Core employee profile, job details, and organizational reporting hierarchy. |
| **`Department`** | `id` (Auto-increment) | `manager_id` (FK to `Employee.id`) | 1:N with `Employee` | Organizational business units and department manager assignments. |
| **`Attendance`** | `id` (Auto-increment) | `employee_id` (FK to `Employee.id`) | N:1 with `Employee` | Daily work shift tracking, check-in, check-out, and auto-computed status. |
| **`LeaveType`** | `id` (Auto-increment) | None | 1:N with `LeaveRequest` | Policy categories (Paid Time Off, Sick Leave, Unpaid Leave). |
| **`LeaveRequest`**| `id` (Auto-increment) | `employee_id` (FK), `leave_type_id` (FK), `reviewed_by` (FK to `User.id`) | N:1 with `Employee`, `LeaveType`, `User` | Leave applications with review status (`Pending`, `Approved`, `Rejected`) and audit comments. |
| **`SalaryStructure`** | `id` (Auto-increment) | `employee_id` (FK to `Employee.id`) | 1:N with `Payslip` | Active and historical compensation breakdowns with effective date ranges. |
| **`Payslip`** | `id` (Auto-increment) | `employee_id` (FK), `salary_structure_id` (FK) | N:1 with `Employee`, `SalaryStructure` | Immutable point-in-time monthly payroll statement snapshots. |
| **`AuditLog`** | `id` (Auto-increment) | `user_id` (FK to `User.id`) | N:1 with `User` | Immutable system event log capturing administrative writes and approvals. |
