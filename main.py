import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api import attendance, auth, departments, employees, leave, payroll
from app.core.database import Base, SessionLocal, engine
from app.core.security import get_password_hash
from app.models.user import User
from app.models.employee import Employee
from app.models.leave import LeaveType
from app.models.department import Department
from app.web import views
from datetime import date

from fastapi.middleware.cors import CORSMiddleware

# Ensure tables are created for quick testing
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dayflow HRMS", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include API routers
app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(attendance.router)
app.include_router(leave.router)
app.include_router(payroll.router)
app.include_router(departments.router)

# Include Web UI Jinja2 templates router
app.include_router(views.router)



@app.on_event("startup")
def seed_initial_data():
    """Seed initial HR Admin and Employee demo users if database is empty."""
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            # 1. Admin HR User
            admin_user = User(
                employee_code="HR001",
                email="hr@company.com",
                password_hash=get_password_hash("admin123"),
                role="admin_hr",
                is_verified=True,
                is_active=True,
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)

            admin_emp = Employee(
                user_id=admin_user.id,
                first_name="Admin",
                last_name="HR",
                job_title="HR Manager",
                joining_date=date(2025, 1, 1),
            )
            db.add(admin_emp)

            # 2. Employee User
            emp_user = User(
                employee_code="EMP001",
                email="employee@company.com",
                password_hash=get_password_hash("emp123"),
                role="employee",
                is_verified=True,
                is_active=True,
            )
            db.add(emp_user)
            db.commit()
            db.refresh(emp_user)

            emp_record = Employee(
                user_id=emp_user.id,
                first_name="John",
                last_name="Doe",
                phone="+1234567890",
                address="123 Innovation Way",
                job_title="Software Developer",
                joining_date=date(2026, 1, 15),
            )
            db.add(emp_record)

            # 3. Default Departments
            dept_eng = Department(name="Engineering", description="Software & System Engineering")
            dept_hr = Department(name="Human Resources", description="People Operations & Talent")
            dept_design = Department(name="Design & UX", description="Product Design & Creative")
            db.add_all([dept_eng, dept_hr, dept_design])
            db.commit()
            db.refresh(dept_eng)
            db.refresh(dept_hr)

            admin_emp.department_id = dept_hr.id
            admin_emp.job_title = "HR Manager & Director"
            emp_record.department_id = dept_eng.id
            emp_record.manager_id = admin_emp.id

            # 4. Default Leave Types
            db.add_all([
                LeaveType(name="Paid Leave", description="Standard paid time off", is_paid=True),
                LeaveType(name="Sick Leave", description="Medical & health leave", is_paid=True),
                LeaveType(name="Unpaid Leave", description="Unpaid leave request", is_paid=False),
            ])
            db.commit()
    finally:
        db.close()
