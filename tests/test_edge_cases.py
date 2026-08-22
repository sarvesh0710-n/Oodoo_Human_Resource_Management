import pytest
from datetime import date, datetime, timedelta, time
from decimal import Decimal
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from app.core.database import Base
from app.core.deps import get_db, get_current_user
from app.core.security import create_access_token, get_password_hash
from app.models.user import User
from app.models.employee import Employee
from app.models.department import Department
from app.models.attendance import Attendance
from app.models.leave import LeaveType, LeaveRequest
from app.models.payroll import SalaryStructure, Payslip
from app.schemas import (
    EmployeeCreate,
    LeaveRequestCreate,
    LeaveRequestReview,
    SalaryStructureCreate,
    PayslipGenerate,
)
from app.services import (
    attendance_service,
    auth_service,
    employee_service,
    leave_service,
    payroll_service,
)
from app.services.guards import assert_not_self_action


@pytest.fixture(scope="module")
def db_engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, echo=False)
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def edge_fixture(db_session):
    user_admin1 = User(
        employee_code="HR_EDGE_1",
        email="hr_edge1@company.com",
        password_hash=get_password_hash("pass"),
        role="admin_hr",
        is_verified=True,
        is_active=True,
    )
    user_admin_no_emp = User(
        employee_code="HR_EDGE_NO_EMP",
        email="hr_no_emp@company.com",
        password_hash=get_password_hash("pass"),
        role="admin_hr",
        is_verified=True,
        is_active=True,
    )
    user_emp1 = User(
        employee_code="EMP_EDGE_1",
        email="emp_edge1@company.com",
        password_hash=get_password_hash("pass"),
        role="employee",
        is_verified=True,
        is_active=True,
    )

    db_session.add_all([user_admin1, user_admin_no_emp, user_emp1])
    db_session.commit()

    emp_admin1 = Employee(user_id=user_admin1.id, first_name="Admin", last_name="One", joining_date=date(2025, 1, 1))
    emp1 = Employee(user_id=user_emp1.id, first_name="Alice", last_name="Edge", joining_date=date(2026, 1, 1))

    db_session.add_all([emp_admin1, emp1])

    leave_type = LeaveType(name="Paid Leave", description="Standard leave", is_paid=True)
    db_session.add(leave_type)
    db_session.commit()

    return {
        "admin1": user_admin1,
        "admin1_emp": emp_admin1,
        "admin_no_emp": user_admin_no_emp,
        "emp1": user_emp1,
        "emp1_record": emp1,
        "leave_type": leave_type,
    }


# ==================== LEAVE EDGE CASES ====================
def test_leave_single_day_request(db_session, edge_fixture):
    # LEAVE EDGE 1: start_date == end_date is valid
    emp1 = edge_fixture["emp1"]
    leave_type = edge_fixture["leave_type"]

    req = leave_service.create_leave_request(
        db_session,
        emp1,
        LeaveRequestCreate(
            leave_type_id=leave_type.id,
            start_date=date(2027, 5, 10),
            end_date=date(2027, 5, 10),
            remarks="Single day leave",
        ),
    )
    assert req.id is not None
    assert req.start_date == req.end_date == date(2027, 5, 10)


def test_leave_overlap_boundary_adjacency(db_session, edge_fixture):
    # LEAVE EDGE 2: Leave ranges are inclusive of start_date and end_date.
    # [May 1, May 5] and [May 5, May 8] overlap on May 5 -> Expected 400.
    # Adjacent [May 1, May 5] and [May 6, May 8] do NOT overlap -> Expected 201.
    emp1 = edge_fixture["emp1"]
    leave_type = edge_fixture["leave_type"]

    # Initial leave: May 1 to May 5
    leave_service.create_leave_request(
        db_session,
        emp1,
        LeaveRequestCreate(leave_type_id=leave_type.id, start_date=date(2027, 5, 1), end_date=date(2027, 5, 5)),
    )

    # Same-day endpoint overlap (May 5 to May 8) -> Rejected 400
    with pytest.raises(HTTPException) as exc_same_day:
        leave_service.create_leave_request(
            db_session,
            emp1,
            LeaveRequestCreate(leave_type_id=leave_type.id, start_date=date(2027, 5, 5), end_date=date(2027, 5, 8)),
        )
    assert exc_same_day.value.status_code == 400

    # Truly adjacent leave (May 6 to May 8) -> Allowed 201
    adjacent_req = leave_service.create_leave_request(
        db_session,
        emp1,
        LeaveRequestCreate(leave_type_id=leave_type.id, start_date=date(2027, 5, 6), end_date=date(2027, 5, 8)),
    )
    assert adjacent_req.id is not None


def test_leave_edit_pending_same_dates(db_session, edge_fixture):
    # LEAVE EDGE 3: Updating a pending leave request to its exact current dates does not flag self-overlap
    emp1 = edge_fixture["emp1"]
    leave_type = edge_fixture["leave_type"]

    req = leave_service.create_leave_request(
        db_session,
        emp1,
        LeaveRequestCreate(leave_type_id=leave_type.id, start_date=date(2027, 6, 1), end_date=date(2027, 6, 3), remarks="Initial"),
    )

    updated = leave_service.update_pending_leave_request(
        db_session,
        emp1,
        req.id,
        LeaveRequestCreate(leave_type_id=leave_type.id, start_date=date(2027, 6, 1), end_date=date(2027, 6, 3), remarks="Updated remarks"),
    )
    assert updated.remarks == "Updated remarks"


def test_leave_year_rollover_attendance_sync(db_session, edge_fixture):
    # LEAVE EDGE 4: Approving leave across Dec 30 to Jan 2 walks year boundary correctly
    emp1 = edge_fixture["emp1"]
    emp1_record = edge_fixture["emp1_record"]
    admin1 = edge_fixture["admin1"]
    leave_type = edge_fixture["leave_type"]

    req = leave_service.create_leave_request(
        db_session,
        emp1,
        LeaveRequestCreate(leave_type_id=leave_type.id, start_date=date(2026, 12, 30), end_date=date(2027, 1, 2)),
    )

    leave_service.review_leave_request(db_session, admin1, req.id, LeaveRequestReview(status="approved"))

    expected_dates = [date(2026, 12, 30), date(2026, 12, 31), date(2027, 1, 1), date(2027, 1, 2)]
    for d in expected_dates:
        att = db_session.query(Attendance).filter(Attendance.employee_id == emp1_record.id, Attendance.date == d).first()
        assert att is not None
        assert att.status == "leave"


def test_leave_leap_year_dates(db_session, edge_fixture):
    # LEAVE EDGE 5: Feb 29 on leap year (2028) handles seamlessly
    emp1 = edge_fixture["emp1"]
    leave_type = edge_fixture["leave_type"]

    req = leave_service.create_leave_request(
        db_session,
        emp1,
        LeaveRequestCreate(leave_type_id=leave_type.id, start_date=date(2028, 2, 28), end_date=date(2028, 2, 29)),
    )
    assert req.id is not None


def test_leave_rejection_does_not_touch_attendance(db_session, edge_fixture):
    # LEAVE EDGE 6: Rejecting a leave request does NOT create attendance rows
    emp1 = edge_fixture["emp1"]
    emp1_record = edge_fixture["emp1_record"]
    admin1 = edge_fixture["admin1"]
    leave_type = edge_fixture["leave_type"]

    req = leave_service.create_leave_request(
        db_session,
        emp1,
        LeaveRequestCreate(leave_type_id=leave_type.id, start_date=date(2027, 7, 10), end_date=date(2027, 7, 12)),
    )

    leave_service.review_leave_request(db_session, admin1, req.id, LeaveRequestReview(status="rejected", review_comment="Not approved"))

    att = db_session.query(Attendance).filter(Attendance.employee_id == emp1_record.id, Attendance.date == date(2027, 7, 10)).first()
    assert att is None


# ==================== ATTENDANCE EDGE CASES ====================
def test_attendance_zero_duration_shift_rejected(db_session, edge_fixture):
    # ATT END EDGE 2: Explicit check_out equal to check_in (zero-duration) is rejected with 400
    emp1 = edge_fixture["emp1"]

    attendance_service.check_in(db_session, emp1, check_in_time=time(9, 0, 0))

    with pytest.raises(HTTPException) as exc_zero:
        attendance_service.check_out(db_session, emp1, check_out_time=time(9, 0, 0))
    assert exc_zero.value.status_code == 400


def test_attendance_query_non_existent_employee_404(db_session, edge_fixture):
    # ATT END EDGE 3: Admin HR querying non-existent employee_id returns 404
    admin1 = edge_fixture["admin1"]

    with pytest.raises(HTTPException) as exc_404:
        attendance_service.get_attendance_records(db_session, admin1, employee_id_param=999999)
    assert exc_404.value.status_code == 404


# ==================== PAYROLL EDGE CASES ====================
def test_payroll_future_salary_structure_not_used_for_past_period(db_session, edge_fixture):
    # PAYROLL EDGE 1: Structure effective in future (Oct 2026) is NOT used for Aug 2026 payslip
    admin1 = edge_fixture["admin1"]
    emp1_record = edge_fixture["emp1_record"]

    # Active structure from Jan 2026 ($5000 basic)
    payroll_service.create_salary_structure(
        db_session,
        admin1,
        SalaryStructureCreate(employee_id=emp1_record.id, basic_salary=Decimal("5000.00"), effective_from=date(2026, 1, 1)),
    )

    # Future structure from Oct 2026 ($8000 basic)
    payroll_service.create_salary_structure(
        db_session,
        admin1,
        SalaryStructureCreate(employee_id=emp1_record.id, basic_salary=Decimal("8000.00"), effective_from=date(2026, 10, 1)),
    )

    # Generate payslip for Month 8 2026 (August) -> Must pick $5000 structure, not future $8000
    ps = payroll_service.generate_payslip(db_session, admin1, PayslipGenerate(employee_id=emp1_record.id, month=8, year=2026))
    assert ps.basic_salary == Decimal("5000.00")


def test_payroll_payslip_before_employee_first_structure_rejected(db_session, edge_fixture):
    # PAYROLL EDGE 2: Payslip period prior to employee's first salary structure returns 400
    admin1 = edge_fixture["admin1"]
    emp1_record = edge_fixture["emp1_record"]

    # First structure effective 2026-06-01
    payroll_service.create_salary_structure(
        db_session,
        admin1,
        SalaryStructureCreate(employee_id=emp1_record.id, basic_salary=Decimal("6000.00"), effective_from=date(2026, 6, 1)),
    )

    # Payslip requested for Month 3 2026 (March, prior to June) -> Expect 400
    with pytest.raises(HTTPException) as exc_before:
        payroll_service.generate_payslip(db_session, admin1, PayslipGenerate(employee_id=emp1_record.id, month=3, year=2026))
    assert exc_before.value.status_code == 400


def test_payroll_zero_allowances_deductions(db_session, edge_fixture):
    # PAYROLL EDGE 3: Allowances/deductions = Decimal("0.00") processed cleanly
    admin1 = edge_fixture["admin1"]
    emp1_record = edge_fixture["emp1_record"]

    payroll_service.create_salary_structure(
        db_session,
        admin1,
        SalaryStructureCreate(
            employee_id=emp1_record.id,
            basic_salary=Decimal("5000.00"),
            allowances=Decimal("0.00"),
            deductions=Decimal("0.00"),
            effective_from=date(2026, 1, 1),
        ),
    )

    ps = payroll_service.generate_payslip(db_session, admin1, PayslipGenerate(employee_id=emp1_record.id, month=9, year=2026))
    assert ps.gross_salary == Decimal("5000.00")
    assert ps.net_salary == Decimal("5000.00")


def test_payroll_negative_net_salary_rejected(db_session, edge_fixture):
    # PAYROLL EDGE 4: Deductions > gross salary (net salary < 0) rejected with 400
    admin1 = edge_fixture["admin1"]
    emp1_record = edge_fixture["emp1_record"]

    with pytest.raises(HTTPException) as exc_neg:
        payroll_service.create_salary_structure(
            db_session,
            admin1,
            SalaryStructureCreate(
                employee_id=emp1_record.id,
                basic_salary=Decimal("3000.00"),
                allowances=Decimal("500.00"),
                deductions=Decimal("4000.00"),
                effective_from=date(2026, 1, 1),
            ),
        )
    assert exc_neg.value.status_code == 400
    assert "exceed gross salary" in exc_neg.value.detail


def test_payroll_monetary_upper_bound_overflow_rejected(db_session, edge_fixture):
    # PAYROLL EDGE 6: Extremely large monetary input (e.g. 1e250) is rejected with 400 Bad Request
    admin1 = edge_fixture["admin1"]
    emp1_record = edge_fixture["emp1_record"]

    with pytest.raises(HTTPException) as exc_overflow:
        payroll_service.create_salary_structure(
            db_session,
            admin1,
            SalaryStructureCreate(
                employee_id=emp1_record.id,
                basic_salary=Decimal("1e250"),
                allowances=Decimal("0.00"),
                deductions=Decimal("0.00"),
                effective_from=date(2026, 1, 1),
            ),
        )
    assert exc_overflow.value.status_code == 400
    assert "cannot exceed" in exc_overflow.value.detail


def test_payroll_non_existent_employee_structure_rejected(db_session, edge_fixture):
    # PAYROLL EDGE 5: Creating salary structure for non-existent employee returns 404
    admin1 = edge_fixture["admin1"]

    with pytest.raises(HTTPException) as exc_404:
        payroll_service.create_salary_structure(
            db_session,
            admin1,
            SalaryStructureCreate(employee_id=999999, basic_salary=Decimal("5000.00"), effective_from=date(2026, 1, 1)),
        )
    assert exc_404.value.status_code == 404


# ==================== RBAC / AUTH EDGE CASES ====================
def test_auth_deleted_user_returns_401(db_session, edge_fixture):
    # RBAC EDGE 1: JWT for user deleted from DB returns 401
    user_temp = User(
        employee_code="TEMP_DEL",
        email="temp_del@company.com",
        password_hash=get_password_hash("pass"),
        role="employee",
        is_verified=True,
        is_active=True,
    )
    db_session.add(user_temp)
    db_session.commit()
    temp_id = user_temp.id
    token = create_access_token({"sub": str(temp_id), "role": "employee"})

    # Delete user from DB
    db_session.delete(user_temp)
    db_session.commit()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401

    app.dependency_overrides.clear()


def test_auth_deactivated_mid_session_returns_401(db_session, edge_fixture):
    # RBAC EDGE 2: User active when token issued, but deactivated mid-session -> 401
    user_active = User(
        employee_code="TEMP_DEACT",
        email="temp_deact@company.com",
        password_hash=get_password_hash("pass"),
        role="employee",
        is_verified=True,
        is_active=True,
    )
    db_session.add(user_active)
    db_session.commit()

    token = create_access_token({"sub": str(user_active.id), "role": "employee"})

    # Flip is_active to False
    user_active.is_active = False
    db_session.commit()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401

    app.dependency_overrides.clear()


def test_auth_malformed_authorization_header(db_session, edge_fixture):
    # RBAC EDGE 3: Malformed Authorization header returns 401
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    # Missing "Bearer " prefix
    r1 = client.get("/api/auth/me", headers={"Authorization": "InvalidTokenString"})
    assert r1.status_code == 401

    # Empty token
    r2 = client.get("/api/auth/me", headers={"Authorization": "Bearer "})
    assert r2.status_code == 401

    # Garbage token payload
    r3 = client.get("/api/auth/me", headers={"Authorization": "Bearer garbage.payload.signature"})
    assert r3.status_code == 401

    app.dependency_overrides.clear()


def test_self_action_guard_admin_no_employee_record_no_crash(db_session, edge_fixture):
    # RBAC EDGE 4: Admin HR without linked Employee record no-ops assert_not_self_action safely
    admin_no_emp = edge_fixture["admin_no_emp"]

    # Should not raise exception or crash
    assert_not_self_action(db_session, admin_no_emp, target_employee_id=1)
