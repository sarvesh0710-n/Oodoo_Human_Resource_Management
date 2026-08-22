#!/usr/bin/env python3
"""
Dayflow HRMS — Comprehensive Database Population Script
Populates departments, HR admins, employees across departments, attendance check-ins/check-outs,
leave requests, and salary structures.

Usage:
    python -m scripts.populate_sample_data
"""
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import User
from app.models.employee import Employee
from app.models.department import Department
from app.models.leave import LeaveType, LeaveRequest
from app.models.attendance import Attendance
from app.models.payroll import SalaryStructure, Payslip


def populate_full_sample_data(db: Session):
    print("==================================================")
    print("   POPULATING COMPREHENSIVE SAMPLE DATA          ")
    print("==================================================")

    # 1. Departments
    print("\n[*] Populating Departments...")
    departments_def = [
        {"name": "Engineering", "description": "Software architecture, backend services, and DevOps infrastructure"},
        {"name": "Human Resources", "description": "Talent acquisition, organizational development, and employee operations"},
        {"name": "Product & UX", "description": "User experience research, UI design, and product roadmap strategy"},
        {"name": "Marketing", "description": "Brand growth, digital campaigns, and community engagement"},
        {"name": "Finance & Legal", "description": "Payroll management, financial auditing, and regulatory compliance"},
    ]
    dept_map = {}
    for d in departments_def:
        dept = db.query(Department).filter(Department.name == d["name"]).first()
        if not dept:
            dept = Department(name=d["name"], description=d["description"])
            db.add(dept)
            db.commit()
            db.refresh(dept)
            print(f"  + Created Department: {dept.name} (ID #{dept.id})")
        else:
            print(f"  . Existing Department: {dept.name} (ID #{dept.id})")
        dept_map[d["name"]] = dept

    # 2. Leave Types
    print("\n[*] Populating Leave Types...")
    leave_types_def = [
        {"name": "Paid Annual Leave", "description": "Standard 14 days annual paid time-off quota", "is_paid": True},
        {"name": "Sick Leave", "description": "Medical, illness, and health recovery time off", "is_paid": True},
        {"name": "Casual Leave", "description": "Short emergency or personal leave", "is_paid": True},
        {"name": "Unpaid Leave", "description": "Extended personal leave without pay", "is_paid": False},
    ]
    lt_map = {}
    for lt in leave_types_def:
        obj = db.query(LeaveType).filter(LeaveType.name == lt["name"]).first()
        if not obj:
            obj = LeaveType(name=lt["name"], description=lt["description"], is_paid=lt["is_paid"])
            db.add(obj)
            db.commit()
            db.refresh(obj)
            print(f"  + Created Leave Type: {obj.name}")
        else:
            print(f"  . Existing Leave Type: {obj.name}")
        lt_map[lt["name"]] = obj

    # 3. HR Admins
    print("\n[*] Populating HR Admins...")
    hrs_def = [
        {
            "email": "hr@company.com",
            "code": "HR_LEAD_01",
            "pass": "admin123",
            "first": "Sarah",
            "last": "Jenkins",
            "title": "Head of Human Resources",
            "dept": dept_map["Human Resources"].id,
        },
        {
            "email": "hr_ops@company.com",
            "code": "HR_OPS_02",
            "pass": "admin123",
            "first": "Michael",
            "last": "Vance",
            "title": "HR Operations Specialist",
            "dept": dept_map["Human Resources"].id,
        },
    ]
    hr_emp_ids = []
    for h in hrs_def:
        u = db.query(User).filter(User.email == h["email"]).first()
        if not u:
            u = User(
                employee_code=h["code"],
                email=h["email"],
                password_hash=get_password_hash(h["pass"]),
                role="admin_hr",
                is_verified=True,
                is_active=True,
            )
            db.add(u)
            db.commit()
            db.refresh(u)
            print(f"  + Created HR Admin: {h['email']}")
        e = db.query(Employee).filter(Employee.user_id == u.id).first()
        if not e:
            e = Employee(
                user_id=u.id,
                department_id=h["dept"],
                first_name=h["first"],
                last_name=h["last"],
                job_title=h["title"],
                phone="+1 (555) 019-2831",
                joining_date=date(2024, 6, 1),
            )
            db.add(e)
            db.commit()
            db.refresh(e)
        hr_emp_ids.append(e.id)

    # 4. Employees across Departments
    print("\n[*] Populating Departmental Employees...")
    emps_def = [
        {
            "email": "employee@company.com",
            "code": "EMP_001",
            "pass": "emp123",
            "first": "Alex",
            "last": "Rivers",
            "title": "Lead Software Engineer",
            "dept": dept_map["Engineering"].id,
            "salary": (Decimal("6500.00"), Decimal("1500.00"), Decimal("500.00")),
        },
        {
            "email": "david.dev@company.com",
            "code": "EMP_ENG_02",
            "pass": "emp123",
            "first": "David",
            "last": "Chen",
            "title": "Backend Systems Developer",
            "dept": dept_map["Engineering"].id,
            "salary": (Decimal("5500.00"), Decimal("1000.00"), Decimal("400.00")),
        },
        {
            "email": "elena.ux@company.com",
            "code": "EMP_UX_03",
            "pass": "emp123",
            "first": "Elena",
            "last": "Rostova",
            "title": "Senior UX Designer",
            "dept": dept_map["Product & UX"].id,
            "salary": (Decimal("5800.00"), Decimal("1100.00"), Decimal("450.00")),
        },
        {
            "email": "marcus.mkt@company.com",
            "code": "EMP_MKT_04",
            "pass": "emp123",
            "first": "Marcus",
            "last": "Thorne",
            "title": "Growth Marketing Manager",
            "dept": dept_map["Marketing"].id,
            "salary": (Decimal("5200.00"), Decimal("900.00"), Decimal("350.00")),
        },
        {
            "email": "sophia.fin@company.com",
            "code": "EMP_FIN_05",
            "pass": "emp123",
            "first": "Sophia",
            "last": "Alvarez",
            "title": "Financial Analyst",
            "dept": dept_map["Finance & Legal"].id,
            "salary": (Decimal("6000.00"), Decimal("1200.00"), Decimal("480.00")),
        },
    ]

    created_employees = []
    for ed in emps_def:
        u = db.query(User).filter(User.email == ed["email"]).first()
        if not u:
            u = User(
                employee_code=ed["code"],
                email=ed["email"],
                password_hash=get_password_hash(ed["pass"]),
                role="employee",
                is_verified=True,
                is_active=True,
            )
            db.add(u)
            db.commit()
            db.refresh(u)
            print(f"  + Created Employee User: {ed['email']}")

        e = db.query(Employee).filter(Employee.user_id == u.id).first()
        if not e:
            e = Employee(
                user_id=u.id,
                department_id=ed["dept"],
                manager_id=hr_emp_ids[0],
                first_name=ed["first"],
                last_name=ed["last"],
                job_title=ed["title"],
                phone="+1 (555) 782-9912",
                joining_date=date(2025, 2, 1),
            )
            db.add(e)
            db.commit()
            db.refresh(e)
        created_employees.append(e)

        # Salary Structure
        st = db.query(SalaryStructure).filter(SalaryStructure.employee_id == e.id).first()
        if not st:
            st = SalaryStructure(
                employee_id=e.id,
                basic_salary=ed["salary"][0],
                allowances=ed["salary"][1],
                deductions=ed["salary"][2],
                effective_from=date(2025, 2, 1),
            )
            db.add(st)
            db.commit()
            print(f"    - Added Salary Structure for {e.first_name} {e.last_name}: ${ed['salary'][0] + ed['salary'][1] - ed['salary'][2]} Net")

    # 5. Department & Employee Attendance Records (Past 5 Days)
    print("\n[*] Populating Attendance Check-ins & Check-outs...")
    today = date.today()
    all_emps = db.query(Employee).all()
    for emp in all_emps:
        for offset in range(5, 0, -1):
            att_date = today - timedelta(days=offset)
            # Skip weekends (5 = Sat, 6 = Sun)
            if att_date.weekday() in (5, 6):
                continue
            existing_att = db.query(Attendance).filter(Attendance.employee_id == emp.id, Attendance.date == att_date).first()
            if not existing_att:
                att = Attendance(
                    employee_id=emp.id,
                    date=att_date,
                    check_in=time(9, 0, 0),
                    check_out=time(17, 30, 0),
                    status="present",
                )
                db.add(att)
                print(f"  + Added Attendance: Emp #{emp.id} on {att_date} (09:00 - 17:30)")
    db.commit()

    # Today's check-in for first employee
    t_att = db.query(Attendance).filter(Attendance.employee_id == created_employees[0].id, Attendance.date == today).first()
    if not t_att:
        t_att = Attendance(
            employee_id=created_employees[0].id,
            date=today,
            check_in=time(8, 55, 0),
            status="present",
        )
        db.add(t_att)
        db.commit()

    # 6. Sample Department & Employee Leave Requests
    print("\n[*] Populating Department & Employee Leave Requests...")
    paid_lt = lt_map["Paid Annual Leave"]
    sick_lt = lt_map["Sick Leave"]

    leave_samples = [
        {
            "emp_id": created_employees[0].id,
            "type_id": paid_lt.id,
            "start": today + timedelta(days=10),
            "end": today + timedelta(days=14),
            "remarks": "Annual family vacation",
            "status": "approved",
            "comment": "Approved by HR",
            "reviewer": hr_emp_ids[0],
        },
        {
            "emp_id": created_employees[1].id,
            "type_id": sick_lt.id,
            "start": today + timedelta(days=2),
            "end": today + timedelta(days=3),
            "remarks": "Medical dental procedure",
            "status": "pending",
            "comment": None,
            "reviewer": None,
        },
    ]

    for ls in leave_samples:
        existing_lr = (
            db.query(LeaveRequest)
            .filter(
                LeaveRequest.employee_id == ls["emp_id"],
                LeaveRequest.start_date == ls["start"],
            )
            .first()
        )
        if not existing_lr:
            lr = LeaveRequest(
                employee_id=ls["emp_id"],
                leave_type_id=ls["type_id"],
                start_date=ls["start"],
                end_date=ls["end"],
                remarks=ls["remarks"],
                status=ls["status"],
                review_comment=ls["comment"],
                reviewed_by=ls["reviewer"],
                reviewed_at=datetime.now() if ls["reviewer"] else None,
            )
            db.add(lr)
            print(f"  + Added Leave Request for Emp #{ls['emp_id']} ({ls['status']})")
    db.commit()

    print("\n==================================================")
    print("[✓] FULL SAMPLE DATA POPULATED SUCCESSFULLY!")
    print("==================================================")


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        populate_full_sample_data(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
