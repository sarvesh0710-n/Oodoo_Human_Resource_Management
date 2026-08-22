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
            # DESIGN DECISION: Querying attendance for a non-existent employee_id returns HTTP 404 instead of a misleading empty list
            target_emp = db.query(Employee).filter(Employee.id == employee_id_param).first()
            if not target_emp:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Employee with ID {employee_id_param} not found",
                )
            return db.query(Attendance).filter(Attendance.employee_id == employee_id_param).all()
        return db.query(Attendance).all()


def check_in(db: Session, current_user: User, check_in_time: Optional[time] = None) -> Attendance:
    emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee record not found")

    # DESIGN DECISION: Midnight boundary date.today() uses server timezone authority consistently
    today = date.today()

    existing = db.query(Attendance).filter(
        Attendance.employee_id == emp.id, Attendance.date == today
    ).first()

    if existing:
        if existing.check_in is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already checked in today",
            )
        now_time = check_in_time if check_in_time is not None else datetime.now().time()
        existing.check_in = now_time
        existing.status = "present"
        db.commit()
        db.refresh(existing)
        return existing

    now_time = check_in_time if check_in_time is not None else datetime.now().time()
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

    existing = db.query(Attendance).filter(
        Attendance.employee_id == emp.id, Attendance.date == today
    ).first()

    if not existing or existing.check_in is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot check out without prior check-in today",
        )

    # DESIGN DECISION: Zero-duration shift (check_out == check_in) is rejected; check_out must be strictly after check_in
    if check_out_time is not None and check_out_time <= existing.check_in:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Check-out time must be strictly after check-in time",
        )

    now_time = check_out_time if check_out_time is not None else datetime.now().time()
    existing.check_out = now_time
    existing.status = "present"
    db.commit()
    db.refresh(existing)
    return existing
