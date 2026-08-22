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
def qa_fixture(db_session):
    # Setup users
    user_admin1 = User(
        employee_code="HR001",
        email="hr1@company.com",
        password_hash=get_password_hash("secret123"),
        role="admin_hr",
        is_verified=True,
        is_active=True,
    )
    user_admin2 = User(
        employee_code="HR002",
        email="hr2@company.com",
        password_hash=get_password_hash("secret123"),
        role="admin_hr",
        is_verified=True,
        is_active=True,
    )
    user_emp1 = User(
        employee_code="EMP001",
        email="emp1@company.com",
        password_hash=get_password_hash("secret123"),
        role="employee",
        is_verified=True,
        is_active=True,
    )
    user_emp2 = User(
        employee_code="EMP002",
        email="emp2@company.com",
        password_hash=get_password_hash("secret123"),
        role="employee",
        is_verified=True,
        is_active=True,
    )
    user_inactive = User(
        employee_code="INACTIVE01",
        email="inactive@company.com",
        password_hash=get_password_hash("secret123"),
        role="employee",
        is_verified=True,
        is_active=False,
    )

    db_session.add_all([user_admin1, user_admin2, user_emp1, user_emp2, user_inactive])
    db_session.commit()

    emp_admin1 = Employee(user_id=user_admin1.id, first_name="Admin", last_name="One", joining_date=date(2025, 1, 1))
    emp_admin2 = Employee(user_id=user_admin2.id, first_name="Admin", last_name="Two", joining_date=date(2025, 1, 1))
    emp1 = Employee(user_id=user_emp1.id, first_name="Alice", last_name="Employee", joining_date=date(2026, 1, 1))
    emp2 = Employee(user_id=user_emp2.id, first_name="Bob", last_name="Employee", joining_date=date(2026, 1, 1))

    db_session.add_all([emp_admin1, emp_admin2, emp1, emp2])

    leave_type = LeaveType(name="Paid Leave", description="Standard paid vacation", is_paid=True)
    db_session.add(leave_type)
    db_session.commit()

    return {
        "admin1": user_admin1,
        "admin1_emp": emp_admin1,
        "admin2": user_admin2,
        "admin2_emp": emp_admin2,
        "emp1": user_emp1,
        "emp1_record": emp1,
        "emp2": user_emp2,
        "emp2_record": emp2,
        "inactive": user_inactive,
        "leave_type": leave_type,
    }


# ==================== 1. LEAVE SERVICE ADVERSARIAL TESTS ====================
def test_leave_overlap_create_and_edit(db_session, qa_fixture):
    emp1 = qa_fixture["emp1"]
    leave_type = qa_fixture["leave_type"]

    # Create initial leave request: 2026-12-01 to 2026-12-05
    req1 = leave_service.create_leave_request(
        db_session,
        emp1,
        LeaveRequestCreate(
            leave_type_id=leave_type.id,
            start_date=date(2026, 12, 1),
            end_date=date(2026, 12, 5),
            remarks="Vacation",
        ),
    )
    assert req1.id is not None

    # Overlap on CREATE (2026-12-03 to 2026-12-08) -> Expect 400
    with pytest.raises(HTTPException) as exc_create:
        leave_service.create_leave_request(
            db_session,
            emp1,
            LeaveRequestCreate(
                leave_type_id=leave_type.id,
                start_date=date(2026, 12, 3),
                end_date=date(2026, 12, 8),
            ),
        )
    assert exc_create.value.status_code == 400
    assert "overlaps" in exc_create.value.detail

    # Create separate non-overlapping request: 2026-12-15 to 2026-12-20
    req2 = leave_service.create_leave_request(
        db_session,
        emp1,
        LeaveRequestCreate(
            leave_type_id=leave_type.id,
            start_date=date(2026, 12, 15),
            end_date=date(2026, 12, 20),
        ),
    )

    # Overlap on EDIT of req2 (moving to 2026-12-04 to 2026-12-16) -> Expect 400
    with pytest.raises(HTTPException) as exc_edit:
        leave_service.update_pending_leave_request(
            db_session,
            emp1,
            req2.id,
            LeaveRequestCreate(
                leave_type_id=leave_type.id,
                start_date=date(2026, 12, 4),
                end_date=date(2026, 12, 16),
            ),
        )
    assert exc_edit.value.status_code == 400
    assert "overlaps" in exc_edit.value.detail


def test_leave_start_date_after_end_date_and_edit_reviewed(db_session, qa_fixture):
    emp1 = qa_fixture["emp1"]
    admin1 = qa_fixture["admin1"]
    leave_type = qa_fixture["leave_type"]

    # start_date > end_date -> Expect 400
    with pytest.raises(HTTPException) as exc_invalid_dates:
        leave_service.create_leave_request(
            db_session,
            emp1,
            LeaveRequestCreate(
                leave_type_id=leave_type.id,
                start_date=date(2026, 12, 10),
                end_date=date(2026, 12, 5),
            ),
        )
    assert exc_invalid_dates.value.status_code == 400

    # Create and approve request
    req = leave_service.create_leave_request(
        db_session,
        emp1,
        LeaveRequestCreate(
            leave_type_id=leave_type.id,
            start_date=date(2026, 12, 22),
            end_date=date(2026, 12, 24),
        ),
    )
    leave_service.review_leave_request(
        db_session, admin1, req.id, LeaveRequestReview(status="approved")
    )

    # Editing approved request -> Expect 403
    with pytest.raises(HTTPException) as exc_edit_approved:
        leave_service.update_pending_leave_request(
            db_session,
            emp1,
            req.id,
            LeaveRequestCreate(
                leave_type_id=leave_type.id,
                start_date=date(2026, 12, 22),
                end_date=date(2026, 12, 25),
            ),
        )
    assert exc_edit_approved.value.status_code == 403


def test_leave_approval_attendance_sync(db_session, qa_fixture):
    emp1 = qa_fixture["emp1"]
    emp1_record = qa_fixture["emp1_record"]
    admin1 = qa_fixture["admin1"]
    leave_type = qa_fixture["leave_type"]

    start = date(2026, 11, 10)
    end = date(2026, 11, 12)

    req = leave_service.create_leave_request(
        db_session,
        emp1,
        LeaveRequestCreate(
            leave_type_id=leave_type.id,
            start_date=start,
            end_date=end,
        ),
    )

    leave_service.review_leave_request(
        db_session, admin1, req.id, LeaveRequestReview(status="approved")
    )

    # Verify exact dates 10, 11, 12 have status='leave'
    for day in range(10, 13):
        att = db_session.query(Attendance).filter(
            Attendance.employee_id == emp1_record.id,
            Attendance.date == date(2026, 11, day),
        ).first()
        assert att is not None
        assert att.status == "leave"

    # Verify date outside range (13 Nov) is untouched
    att_outside = db_session.query(Attendance).filter(
        Attendance.employee_id == emp1_record.id,
        Attendance.date == date(2026, 11, 13),
    ).first()
    assert att_outside is None


# ==================== 2. ATTENDANCE SERVICE ADVERSARIAL TESTS ====================
def test_attendance_double_checkin_checkout_ordering(db_session, qa_fixture):
    emp1 = qa_fixture["emp1"]

    # 1. First Check-in
    att = attendance_service.check_in(db_session, emp1, check_in_time=time(9, 0, 0))
    assert att.check_in == time(9, 0, 0)

    # 2. Double Check-in same day -> Expect 400
    with pytest.raises(HTTPException) as exc_double_in:
        attendance_service.check_in(db_session, emp1, check_in_time=time(9, 30, 0))
    assert exc_double_in.value.status_code == 400

    # 3. Explicit check-out BEFORE check-in (8:00 AM < 9:00 AM) -> Expect 400
    with pytest.raises(HTTPException) as exc_ordering:
        attendance_service.check_out(db_session, emp1, check_out_time=time(8, 0, 0))
    assert exc_ordering.value.status_code == 400

    # 4. Valid check-out (5:00 PM > 9:00 AM)
    att_out = attendance_service.check_out(db_session, emp1, check_out_time=time(17, 0, 0))
    assert att_out.check_out == time(17, 0, 0)


def test_attendance_checkout_without_checkin(db_session, qa_fixture):
    emp2 = qa_fixture["emp2"]

    # Check-out without check-in -> Expect 400
    with pytest.raises(HTTPException) as exc_no_in:
        attendance_service.check_out(db_session, emp2, check_out_time=time(17, 0, 0))
    assert exc_no_in.value.status_code == 400


# ==================== 3. PAYROLL ADVERSARIAL & SNAPSHOT TESTS ====================
def test_payroll_salary_structure_effective_to_closing(db_session, qa_fixture):
    admin1 = qa_fixture["admin1"]
    emp1_record = qa_fixture["emp1_record"]

    # Create structure 1
    s1 = payroll_service.create_salary_structure(
        db_session,
        admin1,
        SalaryStructureCreate(
            employee_id=emp1_record.id,
            basic_salary=Decimal("5000.00"),
            allowances=Decimal("1000.00"),
            deductions=Decimal("500.00"),
            effective_from=date(2026, 1, 1),
        ),
    )
    assert s1.effective_to is None

    # Create structure 2 -> Should auto-close structure 1
    s2 = payroll_service.create_salary_structure(
        db_session,
        admin1,
        SalaryStructureCreate(
            employee_id=emp1_record.id,
            basic_salary=Decimal("6000.00"),
            allowances=Decimal("1200.00"),
            deductions=Decimal("600.00"),
            effective_from=date(2026, 6, 1),
        ),
    )
    db_session.refresh(s1)
    assert s1.effective_to == date(2026, 6, 1)
    assert s2.effective_to is None

    # Verify only ONE active structure has effective_to = NULL
    active_count = db_session.query(SalaryStructure).filter(
        SalaryStructure.employee_id == emp1_record.id,
        SalaryStructure.effective_to.is_(None),
    ).count()
    assert active_count == 1


def test_payroll_payslip_snapshot_and_duplicate_rejection(db_session, qa_fixture):
    admin1 = qa_fixture["admin1"]
    emp1_record = qa_fixture["emp1_record"]

    # Create initial active salary structure
    payroll_service.create_salary_structure(
        db_session,
        admin1,
        SalaryStructureCreate(
            employee_id=emp1_record.id,
            basic_salary=Decimal("6000.00"),
            allowances=Decimal("1200.00"),
            deductions=Decimal("600.00"),
            effective_from=date(2026, 6, 1),
        ),
    )

    # Generate payslip for Month 7 2026 using active structure (basic: 6000)
    ps = payroll_service.generate_payslip(
        db_session,
        admin1,
        PayslipGenerate(employee_id=emp1_record.id, month=7, year=2026),
    )
    assert ps.basic_salary == Decimal("6000.00")
    assert ps.net_salary == Decimal("6600.00")

    # Update salary structure to higher basic (7000)
    payroll_service.create_salary_structure(
        db_session,
        admin1,
        SalaryStructureCreate(
            employee_id=emp1_record.id,
            basic_salary=Decimal("7000.00"),
            allowances=Decimal("1500.00"),
            deductions=Decimal("700.00"),
            effective_from=date(2026, 8, 1),
        ),
    )

    # Verify existing Month 7 payslip snapshot remains UNCHANGED (basic 6000)
    db_session.refresh(ps)
    assert ps.basic_salary == Decimal("6000.00")
    assert ps.net_salary == Decimal("6600.00")

    # Duplicate payslip generation for Month 7 2026 -> Expect 409
    with pytest.raises(HTTPException) as exc_dup:
        payroll_service.generate_payslip(
            db_session,
            admin1,
            PayslipGenerate(employee_id=emp1_record.id, month=7, year=2026),
        )
    assert exc_dup.value.status_code == 409


def test_payroll_payslip_no_active_salary_structure(db_session, qa_fixture):
    admin1 = qa_fixture["admin1"]
    emp2_record = qa_fixture["emp2_record"]

    # Generate payslip for employee without salary structure -> Expect 400
    with pytest.raises(HTTPException) as exc_no_struct:
        payroll_service.generate_payslip(
            db_session,
            admin1,
            PayslipGenerate(employee_id=emp2_record.id, month=8, year=2026),
        )
    assert exc_no_struct.value.status_code == 400


# ==================== 4. RBAC & IDENTITY TRUST ADVERSARIAL TESTS ====================
def test_rbac_admin_endpoints_reject_employee_token(db_session, qa_fixture):
    emp1 = qa_fixture["emp1"]
    emp2_record = qa_fixture["emp2_record"]

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    emp_token = create_access_token({"sub": str(emp1.id), "role": emp1.role})
    headers = {"Authorization": f"Bearer {emp_token}"}

    # 1. Create employee
    r1 = client.post("/api/employees", headers=headers, json={"employee_code": "X", "email": "x@c.com", "password": "p", "first_name": "F", "last_name": "L", "joining_date": "2026-01-01"})
    assert r1.status_code == 403

    # 2. Create department
    r2 = client.post("/api/departments", headers=headers, json={"name": "Finance", "description": "Money"})
    assert r2.status_code == 403

    # 3. Review leave
    r3 = client.patch("/api/leave/requests/1/review", headers=headers, json={"status": "approved"})
    assert r3.status_code == 403

    # 4. Create salary structure
    r4 = client.post("/api/payroll/structures", headers=headers, json={"employee_id": emp2_record.id, "basic_salary": 5000, "effective_from": "2026-01-01"})
    assert r4.status_code == 403

    # 5. Generate payslip
    r5 = client.post("/api/payroll/payslips", headers=headers, json={"employee_id": emp2_record.id, "month": 8, "year": 2026})
    assert r5.status_code == 403

    app.dependency_overrides.clear()


def test_rbac_employee_cannot_query_other_employee_data(db_session, qa_fixture):
    emp1 = qa_fixture["emp1"]
    emp2_record = qa_fixture["emp2_record"]

    # 1. Query attendance with employee_id param for another employee -> Expect 403
    with pytest.raises(HTTPException) as exc1:
        attendance_service.get_attendance_records(db_session, emp1, employee_id_param=emp2_record.id)
    assert exc1.value.status_code == 403

    # 2. Query leave with employee_id param for another employee -> Expect 403
    with pytest.raises(HTTPException) as exc2:
        leave_service.get_leave_requests(db_session, emp1, employee_id_param=emp2_record.id)
    assert exc2.value.status_code == 403

    # 3. Query salary structure for another employee -> Expect 403
    with pytest.raises(HTTPException) as exc3:
        payroll_service.get_salary_structures(db_session, emp1, employee_id_param=emp2_record.id)
    assert exc3.value.status_code == 403

    # 4. Query payslips for another employee -> Expect 403
    with pytest.raises(HTTPException) as exc4:
        payroll_service.get_payslips(db_session, emp1, employee_id_param=emp2_record.id)
    assert exc4.value.status_code == 403


# ==================== 5. SELF-ACTION GUARD (SEC-13) TESTS ====================
def test_self_action_guard_full_cycle(db_session, qa_fixture):
    admin1 = qa_fixture["admin1"]
    admin1_emp = qa_fixture["admin1_emp"]
    admin2 = qa_fixture["admin2"]
    leave_type = qa_fixture["leave_type"]

    # 1. Self leave approval block
    leave_req = leave_service.create_leave_request(
        db_session, admin1, LeaveRequestCreate(leave_type_id=leave_type.id, start_date=date(2026, 12, 28), end_date=date(2026, 12, 30))
    )
    with pytest.raises(HTTPException) as exc_self_leave:
        leave_service.review_leave_request(db_session, admin1, leave_req.id, LeaveRequestReview(status="approved"))
    assert exc_self_leave.value.status_code == 403

    # Peer approval succeeds
    approved = leave_service.review_leave_request(db_session, admin2, leave_req.id, LeaveRequestReview(status="approved"))
    assert approved.status == "approved"

    # 2. Self salary structure creation block
    with pytest.raises(HTTPException) as exc_self_salary:
        payroll_service.create_salary_structure(db_session, admin1, SalaryStructureCreate(employee_id=admin1_emp.id, basic_salary=Decimal("9000.00"), effective_from=date(2026, 1, 1)))
    assert exc_self_salary.value.status_code == 403

    # Peer salary structure creation succeeds
    struct = payroll_service.create_salary_structure(db_session, admin2, SalaryStructureCreate(employee_id=admin1_emp.id, basic_salary=Decimal("9000.00"), effective_from=date(2026, 1, 1)))
    assert struct.id is not None

    # 3. Self payslip generation block
    with pytest.raises(HTTPException) as exc_self_payslip:
        payroll_service.generate_payslip(db_session, admin1, PayslipGenerate(employee_id=admin1_emp.id, month=12, year=2026))
    assert exc_self_payslip.value.status_code == 403

    # Peer payslip generation succeeds
    ps = payroll_service.generate_payslip(db_session, admin2, PayslipGenerate(employee_id=admin1_emp.id, month=12, year=2026))
    assert ps.id is not None


# ==================== 6. AUTHENTICATION ADVERSARIAL TESTS ====================
def test_auth_identical_error_for_wrong_password_and_unknown_email(db_session, qa_fixture):
    # Wrong password
    with pytest.raises(HTTPException) as exc_pw:
        auth_service.authenticate_user(db_session, "emp1@company.com", "wrongpassword")
    
    # Unknown email
    with pytest.raises(HTTPException) as exc_email:
        auth_service.authenticate_user(db_session, "unknown@company.com", "secret123")

    assert exc_pw.value.status_code == 401
    assert exc_email.value.status_code == 401
    assert exc_pw.value.detail == exc_email.value.detail == "Incorrect email or password"


def test_auth_inactive_user_cannot_login(db_session, qa_fixture):
    with pytest.raises(HTTPException) as exc_inactive:
        auth_service.authenticate_user(db_session, "inactive@company.com", "secret123")
    assert exc_inactive.value.status_code == 401
    assert "deactivated" in exc_inactive.value.detail.lower()


def test_auth_tampered_or_expired_jwt_rejected(db_session, qa_fixture):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    # Tampered token
    tampered_headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalidpayload.signature"}
    r1 = client.get("/api/auth/me", headers=tampered_headers)
    assert r1.status_code == 401

    # Expired token (-1 minute)
    expired_token = create_access_token({"sub": "1", "role": "employee"}, expires_delta=timedelta(minutes=-1))
    expired_headers = {"Authorization": f"Bearer {expired_token}"}
    r2 = client.get("/api/auth/me", headers=expired_headers)
    assert r2.status_code == 401

    app.dependency_overrides.clear()
