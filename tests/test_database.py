import unittest
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.user import User
from app.models.department import Department
from app.models.employee import Employee
from app.models.attendance import Attendance
from app.models.leave import LeaveType, LeaveRequest
from app.models.payroll import SalaryStructure, Payslip
from app.models.audit_log import AuditLog


class TestDayflowDatabaseLayer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Use an in-memory SQLite database for testing database models & relationships
        cls.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.session = self.Session()

    def tearDown(self):
        self.session.rollback()
        self.session.close()

    def test_tables_created(self):
        """Verify all 9 tables are present in SQLAlchemy metadata."""
        expected_tables = {
            "user",
            "department",
            "employee",
            "attendance",
            "leave_type",
            "leave_request",
            "salary_structure",
            "payslip",
            "audit_log",
        }
        self.assertEqual(set(Base.metadata.tables.keys()), expected_tables)

    def test_full_crud_and_relationships(self):
        """Test inserting and querying data across all 9 models with relationships."""
        # 1. Create User
        user = User(
            employee_code="EMP001",
            email="john.doe@company.com",
            password_hash="hashed_pw_secret",
            role="admin_hr",
            is_verified=True,
            is_active=True,
        )
        self.session.add(user)
        self.session.commit()
        self.assertIsNotNone(user.id)

        # 2. Create Department
        department = Department(
            name="Engineering",
            description="Software Engineering & Product Development",
        )
        self.session.add(department)
        self.session.commit()
        self.assertIsNotNone(department.id)

        # 3. Create Employee
        employee = Employee(
            user_id=user.id,
            department_id=department.id,
            first_name="John",
            last_name="Doe",
            phone="+1234567890",
            address="123 Tech Lane",
            job_title="Senior Software Engineer",
            joining_date=date(2026, 1, 15),
        )
        self.session.add(employee)
        self.session.commit()

        # Update Department manager_id to employee.id
        department.manager_id = employee.id
        self.session.commit()

        self.assertEqual(employee.user.email, "john.doe@company.com")
        self.assertEqual(employee.department.name, "Engineering")
        self.assertEqual(department.manager.first_name, "John")

        # 4. Create Attendance
        attendance = Attendance(
            employee_id=employee.id,
            date=date(2026, 8, 22),
            check_in=time(9, 0, 0),
            check_out=time(17, 30, 0),
            status="present",
        )
        self.session.add(attendance)
        self.session.commit()
        self.assertEqual(len(employee.attendance_records), 1)

        # 5. Create LeaveType & LeaveRequest
        leave_type = LeaveType(
            name="Annual Leave",
            description="Paid yearly vacation allowance",
            is_paid=True,
        )
        self.session.add(leave_type)
        self.session.commit()

        leave_request = LeaveRequest(
            employee_id=employee.id,
            leave_type_id=leave_type.id,
            reviewed_by=user.id,
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 5),
            remarks="Vacation trip",
            status="approved",
            review_comment="Approved by HR",
            reviewed_at=datetime.now(),
        )
        self.session.add(leave_request)
        self.session.commit()

        self.assertEqual(len(employee.leave_requests), 1)
        self.assertEqual(leave_request.leave_type.name, "Annual Leave")
        self.assertEqual(leave_request.reviewer.email, "john.doe@company.com")

        # 6. Create SalaryStructure & Payslip
        salary_structure = SalaryStructure(
            employee_id=employee.id,
            basic_salary=Decimal("5000.00"),
            allowances=Decimal("1000.00"),
            deductions=Decimal("500.00"),
            effective_from=date(2026, 1, 1),
        )
        self.session.add(salary_structure)
        self.session.commit()

        payslip = Payslip(
            employee_id=employee.id,
            salary_structure_id=salary_structure.id,
            month=8,
            year=2026,
            basic_salary=Decimal("5000.00"),
            allowances=Decimal("1000.00"),
            deductions=Decimal("500.00"),
            gross_salary=Decimal("6000.00"),
            net_salary=Decimal("5500.00"),
        )
        self.session.add(payslip)
        self.session.commit()

        self.assertEqual(len(employee.salary_structures), 1)
        self.assertEqual(len(employee.payslips), 1)
        self.assertEqual(payslip.net_salary, Decimal("5500.00"))

        # 7. Create AuditLog
        audit_log = AuditLog(
            user_id=user.id,
            action="leave_approved",
            entity="leave_request",
            entity_id=leave_request.id,
        )
        self.session.add(audit_log)
        self.session.commit()

        self.assertEqual(len(user.audit_logs), 1)
        self.assertEqual(audit_log.action, "leave_approved")


if __name__ == "__main__":
    unittest.main()
