# Dayflow HRMS — Key Architectural & Design Decisions

This document summarizes the core architectural and design decisions established for **Dayflow HRMS**.

---

## 🏛️ Core Decisions Summary

### 1. Two-Role Model Enforcement
- **Decision**: Standardized strictly on `employee` and `admin_hr` roles.
- **Rationale**: Keeps authorization clean, avoids role proliferation, and satisfies the prompt mandate. No separate `admin` or third-tier role exists.

### 2. Service-Layer RBAC & Identity Derivation
- **Decision**: All authorization checks execute in FastAPI domain service functions (`app/services/*.py`), never relying on frontend state or global middleware alone.
- **Rationale**: Deriving employee identity directly from JWT tokens (`current_user.id`) ensures client-passed `employee_id` parameters cannot breach data boundaries.

### 3. Self-Action Peer Approval Guard (`SEC-13`)
- **Decision**: HR Admins are blocked from approving their own leave requests, setting their own salary structures, or generating their own payslips.
- **Rationale**: Enforces a strict peer-approval model (`assert_not_self_action`), eliminating conflict of interest and self-enrichment vulnerabilities.

### 4. Zero-Gradient Organic Windows UI
- **Decision**: UI built with solid curated HSL colors (`#14382B`, `#1E4D3B`, `#2A6B53`, `#E8F2EE`), zero gradients, standard windows padding, and mobile responsive drawer.
- **Rationale**: Delivers a fast, readable, high-density B2B dashboard experience that feels human and responsive.

### 5. Historical Payslip Snapshotting
- **Decision**: Payslip generation snapshots basic salary, allowances, deductions, gross, and net pay at generation time.
- **Rationale**: Guarantees historical accuracy so future salary structure updates do not alter past payslips.

### 6. Fail-Fast Security Startup
- **Decision**: Application fails fast on startup if `SECRET_KEY` is omitted, requiring explicit environment configuration or `DAYFLOW_ENV=dev`.
- **Rationale**: Prevents silent insecure fallback in production environments.
