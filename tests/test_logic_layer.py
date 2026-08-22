import pytest
from datetime import date, datetime, timedelta, time
from decimal import Decimal
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from app.core.database import Base
from app.core.deps import get_db
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
def seeded_users(db_session):
    # 1. Admin HR #1
    user_admin1 = User(
        employee_code="HR001",
        email="hr1@company.com",
        password_hash=get_password_hash("pass123"),
        role="admin_hr",
        is_verified=True,
        is_active=True,
    )
    # 2. Admin HR #2
    user_admin2 = User(
        employee_code="HR002",
        email="hr2@company.com",
        password_hash=get_password_hash("pass123"),
        role="admin_hr",
        is_verified=True,
        is_active=True,
    )
    # 3. Regular Employee
    user_emp = User(
        employee_code="EMP001",
        email="emp@company.com",
        password_hash=get_password_hash("pass123"),
        role="employee",
        is_verified=True,
        is_active=True,
    )
    # 4. Inactive User
    user_inactive = User(
        employee_code="EMP999",
        email="inactive@company.com",
        password_hash=get_password_hash("pass123"),
        role="employee",
        is_verified=True,
        is_active=False,
    )

    db_session.add_all([user_admin1, user_admin2, user_emp, user_inactive])
    db_session.commit()

    emp_admin1 = Employee(
        user_id=user_admin1.id,
        first_name="Admin",
        last_name="One",
        joining_date=date(2025, 1, 1),
    )
    emp_admin2 = Employee(
        user_id=user_admin2.id,
        first_name="Admin",
        last_name="Two",
        joining_date=date(2025, 1, 1),
    )
    emp_record = Employee(
        user_id=user_emp.id,
        first_name="John",
        last_name="Employee",
        joining_date=date(2026, 1, 15),
    )

    db_session.add_all([emp_admin1, emp_admin2, emp_record])

    leave_type = LeaveType(name="Paid Leave", description="Standard leave", is_paid=True)
    db_session.add(leave_type)
    db_session.commit()

    return {
        "admin1": user_admin1,
        "admin1_emp": emp_admin1,
        "admin2": user_admin2,
        "admin2_emp": emp_admin2,
        "emp": user_emp,
        "emp_record": emp_record,
        "inactive": user_inactive,
        "leave_type": leave_type,
    }


# --- 1. Authentication Tests ---
def test_auth_success(db_session, seeded_users):
    user = auth_service.authenticate_user(db_session, "emp@company.com", "pass123")
    assert user.id == seeded_users["emp"].id


def test_auth_wrong_password(db_session, seeded_users):
    with pytest.raises(HTTPException) as exc_info:
        auth_service.authenticate_user(db_session, "emp@company.com", "wrongpass")
    assert exc_info.value.status_code == 401


def test_auth_wrong_email(db_session, seeded_users):
    with pytest.raises(HTTPException) as exc_info:
        auth_service.authenticate_user(db_session, "nobody@company.com", "pass123")
    assert exc_info.value.status_code == 401


def test_auth_inactive_user(db_session, seeded_users):
    with pytest.raises(HTTPException) as exc_info:
        auth_service.authenticate_user(db_session, "inactive@company.com", "pass123")
    assert exc_info.value.status_code == 401


# --- 2. RBAC Tests ---
def test_rbac_employee_blocked_from_admin_actions(db_session, seeded_users):
    emp_user = seeded_users["emp"]

    # Test API endpoint for create_employee with Employee token
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    emp_token = create_access_token({"sub": str(emp_user.id), "role": emp_user.role})

    res = client.post(
        "/api/employees",
        headers={"Authorization": f"Bearer {emp_token}"},
        json={
            "employee_code": "NEW01",
            "email": "new@company.com",
            "password": "pass",
            "first_name": "Test",
            "last_name": "User",
            "joining_date": "2026-01-01",
        },
    )
    assert res.status_code == 403
    app.dependency_overrides.clear()

    # Employee creating salary structure
    with pytest.raises(HTTPException) as exc2:
        payroll_service.create_salary_structure(
            db_session,
            emp_user,
            SalaryStructureCreate(
                employee_id=seeded_users["emp_record"].id,
                basic_salary=Decimal("4000.00"),
                effective_from=date(2026, 1, 1),
            ),
        )
    assert exc2.value.status_code == 403

    # Employee generating payslip
    with pytest.raises(HTTPException) as exc3:
        payroll_service.generate_payslip(
            db_session,
            emp_user,
            PayslipGenerate(employee_id=seeded_users["emp_record"].id, month=8, year=2026),
        )
    assert exc3.value.status_code == 403

    # Employee reviewing leave
    with pytest.raises(HTTPException) as exc4:
        leave_service.review_leave_request(
            db_session,
            emp_user,
            1,
            LeaveRequestReview(status="approved"),
        )
    assert exc4.value.status_code == 403


# --- 3. Self-Action Guard (SEC-13) Tests ---
def test_self_action_guard_on_leave_review(db_session, seeded_users):
    admin1 = seeded_users["admin1"]
    admin2 = seeded_users["admin2"]
    leave_type = seeded_users["leave_type"]

    # Admin #1 creates a leave request for themselves
    leave_req = leave_service.create_leave_request(
        db_session,
        admin1,
        LeaveRequestCreate(
            leave_type_id=leave_type.id,
            start_date=date(2026, 9, 10),
            end_date=date(2026, 9, 12),
        ),
    )

    # Admin #1 attempts to approve THEIR OWN leave request -> Expect HTTP 403
    with pytest.raises(HTTPException) as exc_info:
        leave_service.review_leave_request(
            db_session,
            admin1,
            leave_req.id,
            LeaveRequestReview(status="approved", review_comment="Self approval attempt"),
        )
    assert exc_info.value.status_code == 403
    assert "Self-action forbidden" in exc_info.value.detail

    # Admin #2 (peer) reviews and approves Admin #1's leave request -> Expect Success
    reviewed = leave_service.review_leave_request(
        db_session,
        admin2,
        leave_req.id,
        LeaveRequestReview(status="approved", review_comment="Peer approved"),
    )
    assert reviewed.status == "approved"
    assert reviewed.reviewed_by == admin2.id


def test_self_action_guard_on_payroll(db_session, seeded_users):
    admin1 = seeded_users["admin1"]
    admin1_emp = seeded_users["admin1_emp"]
    admin2 = seeded_users["admin2"]

    # Admin #1 attempts to create salary structure for themselves -> Expect HTTP 403
    with pytest.raises(HTTPException) as exc1:
        payroll_service.create_salary_structure(
            db_session,
            admin1,
            SalaryStructureCreate(
                employee_id=admin1_emp.id,
                basic_salary=Decimal("8000.00"),
                effective_from=date(2026, 1, 1),
            ),
        )
    assert exc1.value.status_code == 403

    # Admin #2 creates salary structure for Admin #1 -> Expect Success
    struct = payroll_service.create_salary_structure(
        db_session,
        admin2,
        SalaryStructureCreate(
            employee_id=admin1_emp.id,
            basic_salary=Decimal("8000.00"),
            effective_from=date(2026, 1, 1),
        ),
    )
    assert struct.employee_id == admin1_emp.id

    # Admin #1 attempts to generate payslip for themselves -> Expect HTTP 403
    with pytest.raises(HTTPException) as exc2:
        payroll_service.generate_payslip(
            db_session,
            admin1,
            PayslipGenerate(employee_id=admin1_emp.id, month=8, year=2026),
        )
    assert exc2.value.status_code == 403

    # Admin #2 generates payslip for Admin #1 -> Expect Success
    payslip = payroll_service.generate_payslip(
        db_session,
        admin2,
        PayslipGenerate(employee_id=admin1_emp.id, month=8, year=2026),
    )
    assert payslip.employee_id == admin1_emp.id


# --- 4. Leave Overlap Validation Tests ---
def test_leave_overlap_creation_and_editing(db_session, seeded_users):
    emp_user = seeded_users["emp"]
    leave_type = seeded_users["leave_type"]

    # 1. Create first request (10-15 Oct)
    req1 = leave_service.create_leave_request(
        db_session,
        emp_user,
        LeaveRequestCreate(
            leave_type_id=leave_type.id,
            start_date=date(2026, 10, 10),
            end_date=date(2026, 10, 15),
            remarks="Trip",
        ),
    )
    assert req1.id is not None

    # 2. Attempt overlapping request (12-18 Oct) -> Expect HTTP 400
    with pytest.raises(HTTPException) as exc1:
        leave_service.create_leave_request(
            db_session,
            emp_user,
            LeaveRequestCreate(
                leave_type_id=leave_type.id,
                start_date=date(2026, 10, 12),
                end_date=date(2026, 10, 18),
            ),
        )
    assert exc1.value.status_code == 400

    # 3. Create non-overlapping request (20-25 Oct)
    req2 = leave_service.create_leave_request(
        db_session,
        emp_user,
        LeaveRequestCreate(
            leave_type_id=leave_type.id,
            start_date=date(2026, 10, 20),
            end_date=date(2026, 10, 25),
        ),
    )

    # 4. Attempt to edit req2 dates to overlap with req1 (14-22 Oct) -> Expect HTTP 400
    with pytest.raises(HTTPException) as exc2:
        leave_service.update_pending_leave_request(
            db_session,
            emp_user,
            req2.id,
            LeaveRequestCreate(
                leave_type_id=leave_type.id,
                start_date=date(2026, 10, 14),
                end_date=date(2026, 10, 22),
            ),
        )
    assert exc2.value.status_code == 400


# --- 5. Payslip Idempotency Tests ---
def test_payslip_duplicate_idempotency(db_session, seeded_users):
    admin1 = seeded_users["admin1"]
    emp_record = seeded_users["emp_record"]

    payroll_service.create_salary_structure(
        db_session,
        admin1,
        SalaryStructureCreate(
            employee_id=emp_record.id,
            basic_salary=Decimal("5000.00"),
            effective_from=date(2026, 1, 1),
        ),
    )

    # First payslip generation -> 201 Success
    ps1 = payroll_service.generate_payslip(
        db_session,
        admin1,
        PayslipGenerate(employee_id=emp_record.id, month=8, year=2026),
    )
    assert ps1.id is not None

    # Duplicate payslip generation -> Expect HTTP 409 Conflict
    with pytest.raises(HTTPException) as exc_info:
        payroll_service.generate_payslip(
            db_session,
            admin1,
            PayslipGenerate(employee_id=emp_record.id, month=8, year=2026),
        )
    assert exc_info.value.status_code == 409


# --- 6. Attendance Auto-Sync Test ---
def test_attendance_sync_on_leave_approval(db_session, seeded_users):
    emp_user = seeded_users["emp"]
    emp_record = seeded_users["emp_record"]
    admin1 = seeded_users["admin1"]
    leave_type = seeded_users["leave_type"]

    req = leave_service.create_leave_request(
        db_session,
        emp_user,
        LeaveRequestCreate(
            leave_type_id=leave_type.id,
            start_date=date(2026, 11, 1),
            end_date=date(2026, 11, 3),
        ),
    )

    # Approve request
    leave_service.review_leave_request(
        db_session,
        admin1,
        req.id,
        LeaveRequestReview(status="approved"),
    )

    # Verify Attendance rows for 1, 2, 3 Nov 2026 have status='leave'
    for day in range(1, 4):
        att = db_session.query(Attendance).filter(
            Attendance.employee_id == emp_record.id,
            Attendance.date == date(2026, 11, day),
        ).first()
        assert att is not None
        assert att.status == "leave"
