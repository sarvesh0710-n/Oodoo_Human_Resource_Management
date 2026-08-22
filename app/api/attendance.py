from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas import AttendanceCheckIn, AttendanceCheckOut, AttendanceRead
from app.services import attendance_service

router = APIRouter(prefix="/api/attendance", tags=["attendance"])


@router.get("", response_model=List[AttendanceRead])
def get_attendance(
    employee_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return attendance_service.get_attendance_records(db, current_user, employee_id)


@router.post("/check-in", response_model=AttendanceRead, status_code=status.HTTP_201_CREATED)
def check_in(
    payload: Optional[AttendanceCheckIn] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    check_in_time = payload.check_in if payload else None
    return attendance_service.check_in(db, current_user, check_in_time)


@router.post("/check-out", response_model=AttendanceRead)
def check_out(
    payload: Optional[AttendanceCheckOut] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    check_out_time = payload.check_out if payload else None
    return attendance_service.check_out(db, current_user, check_out_time)
