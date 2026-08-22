from datetime import date, datetime, timedelta
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.leave import LeaveRequest, LeaveType
from app.models.user import User
from app.schemas import LeaveRequestCreate, LeaveRequestReview
from app.services.audit_service import log_action


def create_leave_request(db: Session, current_user: User, data: LeaveRequestCreate) -> LeaveRequest:
    emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    # LEAVE-01: start_date > end_date check
    if data.start_date > data.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date cannot be after end date",
        )

    # LEAVE-02: Check overlapping pending/approved requests
    overlapping = db.query(LeaveRequest).filter(
        LeaveRequest.employee_id == emp.id,
        LeaveRequest.status.in_(["pending", "approved"]),
        LeaveRequest.start_date <= data.end_date,
        LeaveRequest.end_date >= data.start_date,
    ).first()

    if overlapping:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Leave request overlaps with an existing pending or approved request",
        )

    leave_req = LeaveRequest(
        employee_id=emp.id,
        leave_type_id=data.leave_type_id,
        start_date=data.start_date,
        end_date=data.end_date,
        remarks=data.remarks,
        status="pending",
    )
    db.add(leave_req)
    db.commit()
    db.refresh(leave_req)
    return leave_req


def get_leave_requests(
    db: Session,
    current_user: User,
    employee_id_param: Optional[int] = None,
) -> List[LeaveRequest]:
    if current_user.role == "employee":
        emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")
        if employee_id_param is not None and employee_id_param != emp.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot query other employees' leave requests",
            )
        return db.query(LeaveRequest).filter(LeaveRequest.employee_id == emp.id).all()
    else:
        if employee_id_param:
            return db.query(LeaveRequest).filter(LeaveRequest.employee_id == employee_id_param).all()
        return db.query(LeaveRequest).all()


def review_leave_request(
    db: Session,
    current_user: User,
    leave_id: int,
    data: LeaveRequestReview,
) -> LeaveRequest:
    # LEAVE-06 / SEC-12: Employee role cannot call approval endpoint
    if current_user.role != "admin_hr":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admin/HR can approve or reject leave requests",
        )

    leave_req = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if not leave_req:
        raise HTTPException(status_code=404, detail="Leave request not found")

    leave_req.status = data.status
    leave_req.review_comment = data.review_comment
    leave_req.reviewed_by = current_user.id
    leave_req.reviewed_at = datetime.now()

    db.commit()

    # LEAVE-07 / Business Rule: On approval, sync Attendance rows with status='leave'
    if data.status == "approved":
        current_dt = leave_req.start_date
        while current_dt <= leave_req.end_date:
            att = db.query(Attendance).filter(
                Attendance.employee_id == leave_req.employee_id,
                Attendance.date == current_dt,
            ).first()

            if att:
                att.status = "leave"
            else:
                att = Attendance(
                    employee_id=leave_req.employee_id,
                    date=current_dt,
                    status="leave",
                )
                db.add(att)
            current_dt += timedelta(days=1)
        db.commit()

    log_action(db, f"leave_{data.status}", "leave_request", leave_req.id, current_user.id)
    db.refresh(leave_req)
    return leave_req


def update_pending_leave_request(
    db: Session,
    current_user: User,
    leave_id: int,
    data: LeaveRequestCreate,
) -> LeaveRequest:
    leave_req = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if not leave_req:
        raise HTTPException(status_code=404, detail="Leave request not found")

    emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()

    # Ownership check
    if current_user.role == "employee" and (not emp or leave_req.employee_id != emp.id):
        raise HTTPException(status_code=403, detail="Access denied")

    # LEAVE-09: Cannot edit already approved/rejected leave
    if leave_req.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot edit a leave request that has already been reviewed",
        )

    leave_req.start_date = data.start_date
    leave_req.end_date = data.end_date
    leave_req.leave_type_id = data.leave_type_id
    leave_req.remarks = data.remarks

    db.commit()
    db.refresh(leave_req)
    return leave_req
