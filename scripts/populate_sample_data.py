#!/usr/bin/env python3
"""
Dayflow HRMS — Comprehensive Database Population Script (randomized)
Populates departments, HR admins, employees across departments, attendance
check-ins/check-outs (with realistic variance), leave requests, and salary
structures.

Usage:
    python -m scripts.populate_sample_data
"""
import random
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

# Fixed seed so a demo run is reproducible if you need to re-run it live,
# but still gives varied-looking data. Delete the seed() call below if you
# want fresh randomness every run.
random.seed(42)

FIRST_NAMES = [
    "Alex", "David", "Elena", "Marcus", "Sophia", "Priya", "Jordan", "Nina",
    "Carlos", "Fatima", "Liam", "Aisha", "Ravi", "Grace", "Tomas", "Yuki",
]
LAST_NAMES = [
    "Rivers", "Chen", "Rostova", "Thorne", "Alvarez", "Nair", "Wells", "Petrov",
    "Mendes", "Khan", "O'Brien", "Bello", "Kapoor", "Lindqvist", "Silva", "Tanaka",
]
JOB_TITLES_BY_DEPT = {
    "Engineering": ["Software Engineer", "Backend Developer", "DevOps Engineer", "QA Engineer", "Engineering Lead"],
    "Human Resources": ["HR Generalist", "Talent Acquisition Specialist", "HR Operations Analyst"],
    "Product & UX": ["UX Designer", "Product Manager", "UI Researcher"],
    "Marketing": ["Marketing Manager", "Content Strategist", "Growth Analyst"],
    "Finance & Legal": ["Financial Analyst", "Payroll Specialist", "Compliance Officer"],
}

# (status, check_in, check_out) templates — check_out=None means "still checked in"
ATTENDANCE_PATTERNS = [
    ("present", time(9, 0, 0), time(17, 30, 0)),
    ("present", time(8, 45, 0), time(17, 15, 0)),
    ("present", time(9, 5, 0), time(18, 0, 0)),
    ("late", time(10, 15, 0), time(18, 30, 0)),
    ("late", time(10, 45, 0), time(17, 45, 0)),
    ("half_day", time(9, 0, 0), time(13, 0, 0)),
    ("absent", None, None),
]
ATTENDANCE_WEIGHTS = [30, 20, 15, 10, 8, 7, 10]  # present-heavy, some absences


def rand_phone():
    return f"+1 ({random.randint(200, 999)}) {random.randint(100, 999)}-{random.randint(1000, 9999)}"


def populate_full_sample_data(db: Session):
    print("==================================================")
    print("   POPULATING COMPREHENSIVE SAMPLE DATA (RANDOM)  ")
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
        {"email": "hr@company.com", "code": "HR_LEAD_01", "pass": "admin123",
         "first": "Sarah", "last": "Jenkins", "title": "Head of Human Resources",
         "dept": dept_map["Human Resources"].id},
        {"email": "hr_ops@company.com", "code": "HR_OPS_02", "pass": "admin123",
         "first": "Michael", "last": "Vance", "title": "HR Operations Specialist",
         "dept": dept_map["Human Resources"].id},
    ]
    hr_emp_ids = []
    for h in hrs_def:
        u = db.query(User).filter(User.email == h["email"]).first()
        if not u:
            u = User(
                employee_code=h["code"], email=h["email"],
                password_hash=get_password_hash(h["pass"]),
                role="admin_hr", is_verified=True, is_active=True,
            )
            db.add(u)
            db.commit()
            db.refresh(u)
            print(f"  + Created HR Admin: {h['email']}")
        e = db.query(Employee).filter(Employee.user_id == u.id).first()
        if not e:
            e = Employee(
                user_id=u.id, department_id=h["dept"],
                first_name=h["first"], last_name=h["last"], job_title=h["title"],
                phone=rand_phone(), joining_date=date(2024, 6, 1),
            )
            db.add(e)
            db.commit()
            db.refresh(e)
        hr_emp_ids.append(e.id)

    # 4. Randomized employees across departments (kept + fixed demo logins,
    # plus extra randomly-generated employees per department for volume)
    print("\n[*] Populating Departmental Employees...")
    fixed_emps_def = [
        {"email": "employee@company.com", "code": "EMP_001", "pass": "emp123",
         "first": "Alex", "last": "Rivers", "title": "Lead Software Engineer",
         "dept": dept_map["Engineering"].id, "salary": (Decimal("6500.00"), Decimal("1500.00"), Decimal("500.00"))},
        {"email": "david.dev@company.com", "code": "EMP_ENG_02", "pass": "emp123",
         "first": "David", "last": "Chen", "title": "Backend Systems Developer",
         "dept": dept_map["Engineering"].id, "salary": (Decimal("5500.00"), Decimal("1000.00"), Decimal("400.00"))},
        {"email": "elena.ux@company.com", "code": "EMP_UX_03", "pass": "emp123",
         "first": "Elena", "last": "Rostova", "title": "Senior UX Designer",
         "dept": dept_map["Product & UX"].id, "salary": (Decimal("5800.00"), Decimal("1100.00"), Decimal("450.00"))},
        {"email": "marcus.mkt@company.com", "code": "EMP_MKT_04", "pass": "emp123",
         "first": "Marcus", "last": "Thorne", "title": "Growth Marketing Manager",
         "dept": dept_map["Marketing"].id, "salary": (Decimal("5200.00"), Decimal("900.00"), Decimal("350.00"))},
        {"email": "sophia.fin@company.com", "code": "EMP_FIN_05", "pass": "emp123",
         "first": "Sophia", "last": "Alvarez", "title": "Financial Analyst",
         "dept": dept_map["Finance & Legal"].id, "salary": (Decimal("6000.00"), Decimal("1200.00"), Decimal("480.00"))},
    ]

    # Generate a handful of extra random employees per department for volume/realism.
    extra_emps_def = []
    used_names = set()
    counter = 6
    for dept_name, dept in dept_map.items():
        if dept_name == "Human Resources":
            continue  # HR already has its two admins
        for _ in range(random.randint(2, 4)):
            fn, ln = None, None
            while (fn, ln) in used_names or fn is None:
                fn, ln = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
            used_names.add((fn, ln))
            code = f"EMP_{dept_name[:3].upper()}_{counter:02d}"
            email = f"{fn.lower()}.{ln.lower().replace(chr(39), '')}{counter}@company.com"
            base = Decimal(random.randint(3800, 7200))
            allowances = (base * Decimal("0.2")).quantize(Decimal("1.00"))
            deductions = (base * Decimal("0.07")).quantize(Decimal("1.00"))
            extra_emps_def.append({
                "email": email, "code": code, "pass": "emp123",
                "first": fn, "last": ln,
                "title": random.choice(JOB_TITLES_BY_DEPT.get(dept_name, ["Staff Member"])),
                "dept": dept.id,
                "salary": (base, allowances, deductions),
            })
            counter += 1

    emps_def = fixed_emps_def + extra_emps_def

    created_employees = []
    for ed in emps_def:
        u = db.query(User).filter(User.email == ed["email"]).first()
        if not u:
            u = User(
                employee_code=ed["code"], email=ed["email"],
                password_hash=get_password_hash(ed["pass"]),
                role="employee", is_verified=True, is_active=True,
            )
            db.add(u)
            db.commit()
            db.refresh(u)
            print(f"  + Created Employee User: {ed['email']}")

        e = db.query(Employee).filter(Employee.user_id == u.id).first()
        if not e:
            e = Employee(
                user_id=u.id, department_id=ed["dept"], manager_id=hr_emp_ids[0],
                first_name=ed["first"], last_name=ed["last"], job_title=ed["title"],
                phone=rand_phone(),
                joining_date=date(2025, random.randint(1, 6), random.randint(1, 28)),
            )
            db.add(e)
            db.commit()
            db.refresh(e)
        created_employees.append(e)

        st = db.query(SalaryStructure).filter(SalaryStructure.employee_id == e.id).first()
        if not st:
            st = SalaryStructure(
                employee_id=e.id,
                basic_salary=ed["salary"][0], allowances=ed["salary"][1], deductions=ed["salary"][2],
                effective_from=date(2025, 2, 1),
            )
            db.add(st)
            db.commit()
            net = ed["salary"][0] + ed["salary"][1] - ed["salary"][2]
            print(f"    - Salary Structure for {e.first_name} {e.last_name}: ${net} Net")

    # 5. Randomized attendance across the past 14 working days
    print("\n[*] Populating Attendance (randomized patterns, last 14 days)...")
    today = date.today()
    all_emps = db.query(Employee).all()
    for emp in all_emps:
        offset = 14
        while offset > 0:
            att_date = today - timedelta(days=offset)
            offset -= 1
            if att_date.weekday() in (5, 6):  # skip weekends
                continue
            existing = db.query(Attendance).filter(
                Attendance.employee_id == emp.id, Attendance.date == att_date
            ).first()
            if existing:
                continue
            status, check_in, check_out = random.choices(ATTENDANCE_PATTERNS, weights=ATTENDANCE_WEIGHTS, k=1)[0]
            att = Attendance(
                employee_id=emp.id,
                date=att_date,
                check_in=check_in,
                check_out=check_out,
                status=status,
            )
            db.add(att)
    db.commit()
    print("  + Attendance records generated for all employees.")

    # A few employees "still checked in" today (no check_out yet) for a live demo feel
    for emp in random.sample(all_emps, k=min(3, len(all_emps))):
        t_att = db.query(Attendance).filter(Attendance.employee_id == emp.id, Attendance.date == today).first()
        if not t_att:
            t_att = Attendance(
                employee_id=emp.id, date=today,
                check_in=time(random.randint(8, 9), random.randint(0, 59), 0),
                status="present",
            )
            db.add(t_att)
    db.commit()

    # 6. Randomized leave requests across employees, types, and statuses
    print("\n[*] Populating Leave Requests (varied statuses)...")
    leave_type_list = list(lt_map.values())
    statuses_weighted = ["approved"] * 4 + ["pending"] * 3 + ["rejected"] * 2

    sample_pool = random.sample(created_employees, k=min(8, len(created_employees)))
    for i, emp in enumerate(sample_pool):
        lt = random.choice(leave_type_list)
        status = random.choice(statuses_weighted)
        start_offset = random.randint(-20, 25)
        span = random.randint(1, 5)
        start = today + timedelta(days=start_offset)
        end = start + timedelta(days=span)

        existing_lr = db.query(LeaveRequest).filter(
            LeaveRequest.employee_id == emp.id, LeaveRequest.start_date == start
        ).first()
        if existing_lr:
            continue

        reviewed = status in ("approved", "rejected")
        lr = LeaveRequest(
            employee_id=emp.id,
            leave_type_id=lt.id,
            start_date=start,
            end_date=end,
            remarks=random.choice([
                "Annual family vacation", "Medical appointment", "Personal matter",
                "Family emergency", "Relocation", "Wedding in family", "Recovery time",
            ]),
            status=status,
            review_comment=("Approved by HR" if status == "approved" else "Insufficient notice" if status == "rejected" else None),
            reviewed_by=(hr_emp_ids[0] if reviewed else None),
            reviewed_at=(datetime.now() if reviewed else None),
        )
        db.add(lr)
        print(f"  + Leave Request for Emp #{emp.id} ({lt.name}, {status})")
    db.commit()

    print("\n==================================================")
    print("[✓] FULL RANDOM SAMPLE DATA POPULATED SUCCESSFULLY!")
    print(f"    Total employees in DB: {len(all_emps)}")
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