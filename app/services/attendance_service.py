from datetime import date, datetime, time
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.user import User


def get_attendance_records(
    db: Session,
    current_user: User,
    employee_id_param: Optional[int] = None,
) -> List[Attendance]:
    # Security Rule: Server derives identity from token for Employee role, never trusts employee_id param
    if current_user.role == "employee":
        emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")
        if employee_id_param is not None and employee_id_param != emp.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot query other employees' attendance",
            )
        return db.query(Attendance).filter(Attendance.employee_id == emp.id).all()
    else:
        # Admin / HR role
        if employee_id_param:
            return db.query(Attendance).filter(Attendance.employee_id == employee_id_param).all()
        return db.query(Attendance).all()


def check_in(db: Session, current_user: User, check_in_time: Optional[time] = None) -> Attendance:
    emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee record not found")

    today = date.today()
    now_time = check_in_time or datetime.now().time()

    existing = db.query(Attendance).filter(
        Attendance.employee_id == emp.id, Attendance.date == today
    ).first()

    if existing:
        if existing.check_in is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already checked in today",
            )
        existing.check_in = now_time
        existing.status = "present"
        db.commit()
        db.refresh(existing)
        return existing

    record = Attendance(
        employee_id=emp.id,
        date=today,
        check_in=now_time,
        status="present",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def check_out(db: Session, current_user: User, check_out_time: Optional[time] = None) -> Attendance:
    emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee record not found")

    today = date.today()
    now_time = check_out_time or datetime.now().time()

    existing = db.query(Attendance).filter(
        Attendance.employee_id == emp.id, Attendance.date == today
    ).first()

    if not existing or existing.check_in is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot check out without prior check-in today",
        )

    existing.check_out = now_time
    existing.status = "present"
    db.commit()
    db.refresh(existing)
    return existing
