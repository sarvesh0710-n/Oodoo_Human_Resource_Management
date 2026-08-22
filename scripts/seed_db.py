#!/usr/bin/env python3
"""
Dayflow HRMS — Database Seeding Script
Usage:
    python -m scripts.seed_db
"""
from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import User
from app.models.employee import Employee
from app.models.department import Department
from app.models.leave import LeaveType
from app.models.payroll import SalaryStructure


def seed_database(db: Session):
    print("==================================================")
    print("         DAYFLOW HRMS DATABASE SEEDING            ")
    print("==================================================")

    # 1. Departments
    print("[*] Seeding Departments...")
    depts_data = [
        {"name": "Engineering", "description": "Software, infrastructure, and technical product development"},
        {"name": "Human Resources", "description": "Talent acquisition, operations, and employee experience"},
        {"name": "Design & UX", "description": "User interface design, brand identity, and design research"},
    ]
    created_depts = []
    for d in depts_data:
        dept = db.query(Department).filter(Department.name == d["name"]).first()
        if not dept:
            dept = Department(name=d["name"], description=d["description"])
            db.add(dept)
            db.commit()
            db.refresh(dept)
            print(f"  + Added Department: '{dept.name}' (ID #{dept.id})")
        else:
            print(f"  . Existing Department: '{dept.name}' (ID #{dept.id})")
        created_depts.append(dept)

    eng_dept = created_depts[0]
    hr_dept = created_depts[1]

    # 2. Leave Types
    print("\n[*] Seeding Leave Types...")
    leave_types_data = [
        {"name": "Paid Leave", "description": "Standard annual paid time-off quota (14 days)", "is_paid": True},
        {"name": "Sick Leave", "description": "Medical and health-related leave", "is_paid": True},
        {"name": "Unpaid Leave", "description": "Extended time off without salary disbursement", "is_paid": False},
    ]
    for lt in leave_types_data:
        existing_lt = db.query(LeaveType).filter(LeaveType.name == lt["name"]).first()
        if not existing_lt:
            new_lt = LeaveType(name=lt["name"], description=lt["description"], is_paid=lt["is_paid"])
            db.add(new_lt)
            db.commit()
            print(f"  + Added Leave Type: '{lt['name']}'")
        else:
            print(f"  . Existing Leave Type: '{lt['name']}'")

    # 3. Default Admin HR User (hr@company.com / admin123)
    print("\n[*] Seeding Admin HR User...")
    admin_user = db.query(User).filter(User.email == "hr@company.com").first()
    if not admin_user:
        admin_user = User(
            employee_code="HR_ADMIN_01",
            email="hr@company.com",
            password_hash=get_password_hash("admin123"),
            role="admin_hr",
            is_verified=True,
            is_active=True,
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print(f"  + Added Admin User: 'hr@company.com' (Password: admin123)")
    else:
        print(f"  . Existing Admin User: 'hr@company.com'")

    admin_emp = db.query(Employee).filter(Employee.user_id == admin_user.id).first()
    if not admin_emp:
        admin_emp = Employee(
            user_id=admin_user.id,
            department_id=hr_dept.id,
            first_name="Admin",
            last_name="HR",
            job_title="HR Lead",
            phone="+1 (555) 100-2000",
            joining_date=date(2025, 1, 1),
        )
        db.add(admin_emp)
        db.commit()

    # 4. Standard Employee User (employee@company.com / emp123)
    print("\n[*] Seeding Standard Employee User...")
    emp_user = db.query(User).filter(User.email == "employee@company.com").first()
    if not emp_user:
        emp_user = User(
            employee_code="EMP_001",
            email="employee@company.com",
            password_hash=get_password_hash("emp123"),
            role="employee",
            is_verified=True,
            is_active=True,
        )
        db.add(emp_user)
        db.commit()
        db.refresh(emp_user)
        print(f"  + Added Employee User: 'employee@company.com' (Password: emp123)")
    else:
        print(f"  . Existing Employee User: 'employee@company.com'")

    emp_rec = db.query(Employee).filter(Employee.user_id == emp_user.id).first()
    if not emp_rec:
        emp_rec = Employee(
            user_id=emp_user.id,
            department_id=eng_dept.id,
            manager_id=admin_emp.id,
            first_name="John",
            last_name="Doe",
            job_title="Senior Software Engineer",
            phone="+1 (555) 234-5678",
            joining_date=date(2026, 1, 15),
        )
        db.add(emp_rec)
        db.commit()

    # 5. Salary Structure for Standard Employee
    print("\n[*] Seeding Salary Structure...")
    struct = db.query(SalaryStructure).filter(SalaryStructure.employee_id == emp_rec.id).first()
    if not struct:
        struct = SalaryStructure(
            employee_id=emp_rec.id,
            basic_salary=Decimal("5000.00"),
            allowances=Decimal("1200.00"),
            deductions=Decimal("450.00"),
            effective_from=date(2026, 1, 1),
        )
        db.add(struct)
        db.commit()
        print(f"  + Added Salary Structure for Employee #{emp_rec.id}: Basic=$5,000, Net=$5,750")
    else:
        print(f"  . Existing Salary Structure for Employee #{emp_rec.id}")

    print("\n==================================================")
    print("[✓] DATABASE SEEDING COMPLETED SUCCESSFULLY!")
    print("==================================================")


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
