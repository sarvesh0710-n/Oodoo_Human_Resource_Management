from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.user import User


def assert_not_self_action(db: Session, current_user: User, target_employee_id: int):
    """
    SEC-13: Self-action guard.
    An admin_hr user cannot perform administrative actions (review leave request, set salary structure,
    generate payslip) on their own employee record.
    Raises HTTP 403 Forbidden if current_user's Employee.id matches target_employee_id.
    """
    if current_user.role == "admin_hr":
        emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if emp and emp.id == target_employee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Self-action forbidden: Admin HR cannot perform administrative actions on their own record",
            )
