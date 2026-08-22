from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas import (
    PayslipGenerate,
    PayslipRead,
    SalaryStructureCreate,
    SalaryStructureRead,
)
from app.services import payroll_service

router = APIRouter(prefix="/api/payroll", tags=["payroll"])


# --- Salary Structures ---
@router.get("/structures", response_model=List[SalaryStructureRead])
def list_salary_structures(
    employee_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return payroll_service.get_salary_structures(db, current_user, employee_id)


@router.post("/structures", response_model=SalaryStructureRead, status_code=status.HTTP_201_CREATED)
def create_salary_structure(
    payload: SalaryStructureCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return payroll_service.create_salary_structure(db, current_user, payload)


# --- Payslips ---
@router.get("/payslips", response_model=List[PayslipRead])
def list_payslips(
    employee_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return payroll_service.get_payslips(db, current_user, employee_id)


@router.post("/payslips", response_model=PayslipRead, status_code=status.HTTP_201_CREATED)
def generate_payslip(
    payload: PayslipGenerate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return payroll_service.generate_payslip(db, current_user, payload)


@router.get("/payslips/{payslip_id}", response_model=PayslipRead)
def get_payslip_by_id(
    payslip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return payroll_service.get_payslip_by_id(db, current_user, payslip_id)
