from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_employee, get_current_user, get_db, require_role
from app.models.employee import Employee
from app.models.user import User
from app.schemas import EmployeeCreate, EmployeeRead, EmployeeUpdateAdmin, EmployeeUpdateSelf
from app.services import employee_service

router = APIRouter(prefix="/api/employees", tags=["employees"])


@router.get("/me", response_model=EmployeeRead)
def read_own_employee_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee record not found")
    return emp


@router.patch("/me", response_model=EmployeeRead)
def update_own_employee_profile(
    payload: EmployeeUpdateSelf,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return employee_service.update_employee_self(db, current_user, payload)


@router.get("", response_model=List[EmployeeRead])
def list_all_employees(
    current_user: User = Depends(require_role(["admin_hr"])),
    db: Session = Depends(get_db),
):
    return employee_service.list_employees(db)


@router.post("", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_employee(
    payload: EmployeeCreate,
    current_user: User = Depends(require_role(["admin_hr"])),
    db: Session = Depends(get_db),
):
    return employee_service.create_employee_with_user(db, payload)


@router.get("/{employee_id}", response_model=EmployeeRead)
def get_employee_by_id(
    employee_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # SEC-01 / SEC-02: Employee can read own record, but not other employees' records
    if current_user.role == "employee":
        emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not emp or emp.id != employee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot view another employee's record",
            )
        return emp
    return employee_service.get_employee_by_id(db, employee_id)


@router.patch("/{employee_id}", response_model=EmployeeRead)
def update_employee_by_admin(
    employee_id: int,
    payload: EmployeeUpdateAdmin,
    current_user: User = Depends(require_role(["admin_hr"])),
    db: Session = Depends(get_db),
):
    return employee_service.update_employee_admin(db, employee_id, payload)
