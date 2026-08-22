from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_role
from app.models.department import Department
from app.models.employee import Employee
from app.models.user import User

router = APIRouter(prefix="/api/departments", tags=["departments"])


class DepartmentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    manager_id: Optional[int] = None


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    manager_id: Optional[int] = None


class DepartmentRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    manager_id: Optional[int] = None
    employee_count: Optional[int] = 0

    class Config:
        from_attributes = True


@router.get("", response_model=List[DepartmentRead])
def list_departments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    depts = db.query(Department).all()
    result = []
    for d in depts:
        count = db.query(Employee).filter(Employee.department_id == d.id).count()
        result.append(
            DepartmentRead(
                id=d.id,
                name=d.name,
                description=d.description,
                manager_id=d.manager_id,
                employee_count=count,
            )
        )
    return result


@router.post("", response_model=DepartmentRead, status_code=status.HTTP_201_CREATED)
def create_department(
    payload: DepartmentCreate,
    current_user: User = Depends(require_role(["admin_hr"])),
    db: Session = Depends(get_db),
):
    dept = Department(
        name=payload.name,
        description=payload.description,
        manager_id=payload.manager_id,
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return DepartmentRead(
        id=dept.id,
        name=dept.name,
        description=dept.description,
        manager_id=dept.manager_id,
        employee_count=0,
    )


@router.patch("/{department_id}", response_model=DepartmentRead)
def update_department(
    department_id: int,
    payload: DepartmentUpdate,
    current_user: User = Depends(require_role(["admin_hr"])),
    db: Session = Depends(get_db),
):
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    if payload.name is not None:
        dept.name = payload.name
    if payload.description is not None:
        dept.description = payload.description
    dept.manager_id = payload.manager_id

    db.commit()
    db.refresh(dept)

    count = db.query(Employee).filter(Employee.department_id == dept.id).count()
    return DepartmentRead(
        id=dept.id,
        name=dept.name,
        description=dept.description,
        manager_id=dept.manager_id,
        employee_count=count,
    )
