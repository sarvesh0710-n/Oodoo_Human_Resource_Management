# Dayflow HRMS — Architecture

## Overview

Dayflow is a custom Odoo module (`dayflow_hrms`) built for an 8-hour hackathon.
It digitizes employee onboarding, profile management, attendance, leave
management, and payroll visibility, with strict role-based access control.

Core design principle: **extend Odoo's existing HR models, don't duplicate
them.** Odoo already ships `res.users`, `hr.employee`, `hr.department`,
`hr.job`, `hr.attendance`, `hr.leave`, and `hr.leave.type`. We inherit and
extend these instead of building parallel tables, and add only two genuinely
new models where Odoo has no equivalent: salary structures and payslips.

## Module dependencies

```
depends = ['base', 'hr', 'hr_attendance', 'hr_holidays']
```

No Enterprise payroll app dependency — payroll is built as a lightweight
custom addition, since Enterprise HR/Payroll may not be available in the
hackathon environment.

## Layers

```
Views (XML)           -- role-specific forms, lists, menus
   |
Access layer           -- security groups + record rules (server-enforced)
   |
Business logic (Python) -- models/*.py, validation, computed fields, workflows
   |
ORM                     -- Odoo's model layer, generates schema
   |
PostgreSQL              -- Odoo's only supported backend, auto-managed
```

The frontend never enforces permissions on its own — record rules and
`ir.model.access.csv` do that at the ORM/DB layer, so even direct
API/URL manipulation can't bypass access control.

## Models

### Inherited (no new tables)
| Model | Odoo base | What we extend |
|---|---|---|
| `res.users` | built-in | nothing structural — auth stays native |
| `hr.employee` | built-in | linked via existing `user_id`, `department_id`, `job_id`, `parent_id` (manager) |
| `hr.department` | built-in | used as-is |
| `hr.job` | built-in | used as-is |
| `hr.attendance` | built-in | leave-sync logic, tested constraints |
| `hr.leave` | built-in | approval workflow via existing `state` field |
| `hr.leave.type` | built-in | used as-is (Paid / Sick / Unpaid) |

### New custom models
| Model | Purpose |
|---|---|
| `hrms.salary.structure` | Time-bound salary components per employee (basic/allowances/deductions), history-preserving |
| `hrms.payslip` | Immutable monthly snapshot generated from a salary structure |

## Security architecture

Two custom groups:
- `Dayflow: Employee` — access to own records only
- `Dayflow: HR Officer` — access to all employee records, approval rights

Enforced via:
- `security/security_groups.xml` — group definitions
- `security/ir.model.access.csv` — per-model CRUD access per group
- `security/record_rules.xml` — row-level domain filters
  (e.g. `[('employee_id.user_id', '=', user.id)]` for Employee group)

## Attendance status — derived, not stored

No `status` column on attendance. Status is computed from data:
- check_in + check_out present → Present
- check_in present, check_out absent → currently checked in
- no record for a working day → Absent
- approved `hr.leave` covering the date → Leave (written by leave-sync logic)

## Leave → Attendance sync

On leave approval (`state` → `validate`), an automated action/override
upserts `hr.attendance` rows for each date in the leave's range, so
attendance and leave records never drift out of sync.

## Payroll design rationale

Payslips store a **snapshot** of salary fields (basic/allowances/deductions)
at generation time, not a live reference to `hrms.salary.structure`. This
guarantees historical accuracy: if an employee's salary changes in March,
their January payslip must still show January's numbers.

## Frontend / UX

- Role-specific menus (`views/menus.xml`) — Employee and HR/Admin see
  different top-level items, matching what they're actually permitted to do.
- Standard Odoo form/list/kanban views, extended not replaced.
- Dashboard view (`dashboard_views.xml`) — attendance summary, pending
  leave count, using Odoo's built-in aggregation, no external charting lib.

## Third-party APIs

None required for core functionality. Optional/nice-to-have: email
notification on leave approval, using Odoo's built-in mail templates
(not an external service).
