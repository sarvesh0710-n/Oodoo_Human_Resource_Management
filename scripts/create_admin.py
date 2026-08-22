#!/usr/bin/env python3
"""
Dayflow HRMS — Admin HR User Creation Script
Usage:
    python -m scripts.create_admin --email hr@company.com --password admin123 --first-name "Alice" --last-name "Smith"
"""
import argparse
import sys
from datetime import date
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import User
from app.models.employee import Employee


def create_or_promote_admin(
    db: Session,
    email: str,
    password: str,
    employee_code: str = None,
    first_name: str = "HR",
    last_name: str = "Admin",
) -> User:
    email = email.strip().lower()
    user = db.query(User).filter(User.email == email).first()

    if user:
        print(f"[*] User with email '{email}' already exists (ID: {user.id}). Updating to admin_hr...")
        user.role = "admin_hr"
        user.password_hash = get_password_hash(password)
        user.is_active = True
        user.is_verified = True
        db.commit()
        db.refresh(user)
        print(f"[✓] User '{email}' successfully promoted to 'admin_hr' role!")
        return user

    if not employee_code:
        employee_code = f"HR_{email.split('@')[0].upper()[:8]}"

    # Ensure employee_code is unique
    existing_code = db.query(User).filter(User.employee_code == employee_code).first()
    if existing_code:
        employee_code = f"{employee_code}_{db.query(User).count() + 1}"

    print(f"[*] Creating new Admin HR user: {email} ({employee_code})...")
    new_user = User(
        employee_code=employee_code,
        email=email,
        password_hash=get_password_hash(password),
        role="admin_hr",
        is_verified=True,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create linked Employee record
    emp_record = db.query(Employee).filter(Employee.user_id == new_user.id).first()
    if not emp_record:
        emp_record = Employee(
            user_id=new_user.id,
            first_name=first_name,
            last_name=last_name,
            job_title="HR Administrator",
            joining_date=date.today(),
        )
        db.add(emp_record)
        db.commit()

    print(f"[✓] Successfully created Admin HR user '{email}' with Employee ID #{emp_record.id}!")
    return new_user


def main():
    parser = argparse.ArgumentParser(description="Create or promote an Admin HR user in Dayflow HRMS.")
    parser.add_argument("--email", type=str, help="Work email address of the admin user")
    parser.add_argument("--password", type=str, help="Account password")
    parser.add_argument("--code", type=str, help="Employee code (optional)", default=None)
    parser.add_argument("--first-name", type=str, help="First name", default="Admin")
    parser.add_argument("--last-name", type=str, help="Last name", default="HR")

    args = parser.parse_args()

    email = args.email or input("Enter Admin Email (e.g. hr@company.com): ").strip()
    password = args.password or input("Enter Admin Password: ").strip()

    if not email or not password:
        print("[!] Error: Email and password are required.", file=sys.stderr)
        sys.exit(1)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        create_or_promote_admin(
            db,
            email=email,
            password=password,
            employee_code=args.code,
            first_name=args.first_name,
            last_name=args.last_name,
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
