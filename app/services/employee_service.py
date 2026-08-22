from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.user import User
from app.schemas import EmployeeCreate, EmployeeUpdateAdmin, EmployeeUpdateSelf
from app.services.auth_service import create_user


def get_employee_by_id(db: Session, employee_id: int) -> Employee:
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with ID {employee_id} not found",
        )
    return emp


def list_employees(db: Session) -> List[Employee]:
    return db.query(Employee).all()


def create_employee_with_user(db: Session, data: EmployeeCreate) -> Employee:
    # 1. Create underlying User
    user = create_user(
        db,
        employee_code=data.employee_code,
        email=data.email,
        password=data.password,
        role=data.role,
    )
    # 2. Create Employee profile
    employee = Employee(
        user_id=user.id,
        department_id=data.department_id,
        manager_id=data.manager_id,
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
        address=data.address,
        job_title=data.job_title,
        joining_date=data.joining_date,
        profile_picture=data.profile_picture,
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


def update_employee_self(db: Session, current_user: User, data: EmployeeUpdateSelf) -> Employee:
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee profile not found",
        )
    if data.phone is not None:
        employee.phone = data.phone
    if data.address is not None:
        employee.address = data.address
    if data.profile_picture is not None:
        employee.profile_picture = data.profile_picture

    db.commit()
    db.refresh(employee)
    return employee


def update_employee_admin(db: Session, employee_id: int, data: EmployeeUpdateAdmin) -> Employee:
    employee = get_employee_by_id(db, employee_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(employee, field, value)
    db.commit()
    db.refresh(employee)
    return employee
