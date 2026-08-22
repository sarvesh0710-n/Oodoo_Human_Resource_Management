from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.leave import LeaveType
from app.models.user import User
from app.schemas import LeaveRequestCreate, LeaveRequestRead, LeaveRequestReview, LeaveTypeRead
from app.services import leave_service

router = APIRouter(prefix="/api/leave", tags=["leave"])


@router.get("/types", response_model=List[LeaveTypeRead])
def list_leave_types(db: Session = Depends(get_db)):
    return db.query(LeaveType).all()


@router.get("/requests", response_model=List[LeaveRequestRead])
def list_leave_requests(
    employee_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return leave_service.get_leave_requests(db, current_user, employee_id)


@router.post("/requests", response_model=LeaveRequestRead, status_code=status.HTTP_201_CREATED)
def submit_leave_request(
    payload: LeaveRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return leave_service.create_leave_request(db, current_user, payload)


@router.patch("/requests/{leave_id}/review", response_model=LeaveRequestRead)
def review_leave(
    leave_id: int,
    payload: LeaveRequestReview,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return leave_service.review_leave_request(db, current_user, leave_id, payload)


@router.patch("/requests/{leave_id}", response_model=LeaveRequestRead)
def update_pending_leave(
    leave_id: int,
    payload: LeaveRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return leave_service.update_pending_leave_request(db, current_user, leave_id, payload)


@router.get("/analytics/department-summary")
def get_department_leave_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models.department import Department
    from app.models.employee import Employee
    from app.models.leave import LeaveRequest

    depts = db.query(Department).all()
    result = []
    for d in depts:
        count = (
            db.query(LeaveRequest)
            .join(Employee, LeaveRequest.employee_id == Employee.id)
            .filter(Employee.department_id == d.id)
            .count()
        )
        result.append(
            {
                "department_id": d.id,
                "department_name": d.name,
                "leave_count": count,
            }
        )
    return result
