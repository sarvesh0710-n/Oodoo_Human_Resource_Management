#!/usr/bin/env python3
"""
Dayflow HRMS — General User Creation Script
Usage:
    python -m scripts.create_user --email emp@company.com --password emp123 --role employee --first-name "Jane" --last-name "Doe" --job-title "Software Engineer"
"""
import argparse
import sys
from datetime import date
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import User
from app.models.employee import Employee
from app.models.department import Department


def create_user(
    db: Session,
    email: str,
    password: str,
    role: str = "employee",
    employee_code: str = None,
    first_name: str = "Jane",
    last_name: str = "Doe",
    job_title: str = "Staff Member",
    department_id: int = None,
    phone: str = None,
) -> User:
    email = email.strip().lower()
    if role not in ("employee", "admin_hr"):
        raise ValueError(f"Invalid role '{role}'. Must be 'employee' or 'admin_hr'.")

    user = db.query(User).filter(User.email == email).first()
    if user:
        print(f"[*] User with email '{email}' already exists (ID: {user.id}). Updating profile...")
        user.role = role
        user.password_hash = get_password_hash(password)
        db.commit()
        db.refresh(user)
    else:
        if not employee_code:
            prefix = "HR" if role == "admin_hr" else "EMP"
            employee_code = f"{prefix}_{email.split('@')[0].upper()[:8]}"
            count = db.query(User).count()
            if db.query(User).filter(User.employee_code == employee_code).first():
                employee_code = f"{employee_code}_{count + 1}"

        print(f"[*] Creating new user: {email} ({role}, {employee_code})...")
        user = User(
            employee_code=employee_code,
            email=email,
            password_hash=get_password_hash(password),
            role=role,
            is_verified=True,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Linked Employee record
    emp = db.query(Employee).filter(Employee.user_id == user.id).first()
    if not emp:
        emp = Employee(
            user_id=user.id,
            department_id=department_id,
            first_name=first_name,
            last_name=last_name,
            job_title=job_title,
            phone=phone,
            joining_date=date.today(),
        )
        db.add(emp)
        db.commit()
        db.refresh(emp)
    else:
        emp.first_name = first_name
        emp.last_name = last_name
        emp.job_title = job_title
        if department_id:
            emp.department_id = department_id
        if phone:
            emp.phone = phone
        db.commit()

    print(f"[✓] Successfully created/updated user '{email}' (Role: {role}, Employee ID: #{emp.id})!")
    return user


def main():
    parser = argparse.ArgumentParser(description="Create a user in Dayflow HRMS.")
    parser.add_argument("--email", type=str, required=True, help="Work email address")
    parser.add_argument("--password", type=str, required=True, help="Account password")
    parser.add_argument("--role", type=str, choices=["employee", "admin_hr"], default="employee", help="User role")
    parser.add_argument("--code", type=str, help="Employee code", default=None)
    parser.add_argument("--first-name", type=str, help="First name", default="Jane")
    parser.add_argument("--last-name", type=str, help="Last name", default="Doe")
    parser.add_argument("--job-title", type=str, help="Job title", default="Staff Member")
    parser.add_argument("--dept-id", type=int, help="Department ID", default=None)
    parser.add_argument("--phone", type=str, help="Phone number", default=None)

    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        create_user(
            db,
            email=args.email,
            password=args.password,
            role=args.role,
            employee_code=args.code,
            first_name=args.first_name,
            last_name=args.last_name,
            job_title=args.job_title,
            department_id=args.dept_id,
            phone=args.phone,
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
