import calendar
from datetime import date
from decimal import Decimal
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.payroll import Payslip, SalaryStructure
from app.models.user import User
from app.schemas import PayslipGenerate, SalaryStructureCreate
from app.services.audit_service import log_action
from app.services.guards import assert_not_self_action


def create_salary_structure(
    db: Session,
    current_user: User,
    data: SalaryStructureCreate,
) -> SalaryStructure:
    # SEC-04 / SEC-07: Admin/HR only
    if current_user.role != "admin_hr":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admin/HR can create or update salary structures",
        )

    # SEC-13: Self-action guard check
    assert_not_self_action(db, current_user, data.employee_id)

    # DESIGN DECISION: Creating a salary structure for a non-existent employee_id returns HTTP 404 instead of a database FK failure
    target_emp = db.query(Employee).filter(Employee.id == data.employee_id).first()
    if not target_emp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with ID {data.employee_id} not found",
        )

    # DESIGN DECISION: Negative net salary (deductions > basic + allowances) is invalid and rejected with HTTP 400
    gross = data.basic_salary + data.allowances
    if data.deductions > gross:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Deductions (${data.deductions:.2f}) cannot exceed gross salary (${gross:.2f})",
        )

    # SEC-09: Close previous active structure (effective_to = null)
    active_structure = db.query(SalaryStructure).filter(
        SalaryStructure.employee_id == data.employee_id,
        SalaryStructure.effective_to.is_(None),
    ).first()

    if active_structure:
        active_structure.effective_to = data.effective_from

    new_structure = SalaryStructure(
        employee_id=data.employee_id,
        basic_salary=data.basic_salary,
        allowances=data.allowances,
        deductions=data.deductions,
        effective_from=data.effective_from,
        effective_to=None,
    )
    db.add(new_structure)
    db.commit()

    log_action(db, "salary_updated", "salary_structure", new_structure.id, current_user.id)
    db.refresh(new_structure)
    return new_structure


def get_salary_structures(
    db: Session,
    current_user: User,
    employee_id_param: Optional[int] = None,
) -> List[SalaryStructure]:
    if current_user.role == "employee":
        emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")
        if employee_id_param is not None and employee_id_param != emp.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot query other employees' salary structures",
            )
        return db.query(SalaryStructure).filter(SalaryStructure.employee_id == emp.id).all()
    else:
        if employee_id_param:
            target_emp = db.query(Employee).filter(Employee.id == employee_id_param).first()
            if not target_emp:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Employee with ID {employee_id_param} not found",
                )
            return db.query(SalaryStructure).filter(SalaryStructure.employee_id == employee_id_param).all()
        return db.query(SalaryStructure).all()


def generate_payslip(
    db: Session,
    current_user: User,
    data: PayslipGenerate,
) -> Payslip:
    # SEC-05: Only Admin/HR can generate payslips
    if current_user.role != "admin_hr":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admin/HR can generate payslips",
        )

    # SEC-13: Self-action guard check
    assert_not_self_action(db, current_user, data.employee_id)

    # SEC-10: Check unique (employee_id, month, year)
    existing = db.query(Payslip).filter(
        Payslip.employee_id == data.employee_id,
        Payslip.month == data.month,
        Payslip.year == data.year,
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Payslip for employee {data.employee_id} for {data.month}/{data.year} already exists",
        )

    # DESIGN DECISION: Salary structure must have effective_from <= target period end date
    last_day = calendar.monthrange(data.year, data.month)[1]
    period_start = date(data.year, data.month, 1)
    period_end = date(data.year, data.month, last_day)

    salary_struct = db.query(SalaryStructure).filter(
        SalaryStructure.employee_id == data.employee_id,
        SalaryStructure.effective_from <= period_end,
        (SalaryStructure.effective_to.is_(None) | (SalaryStructure.effective_to >= period_start)),
    ).order_by(SalaryStructure.effective_from.desc()).first()

    if not salary_struct:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No active salary structure found for employee {data.employee_id} for period {data.month}/{data.year}",
        )

    # Calculate gross & net salary snapshot
    gross = salary_struct.basic_salary + salary_struct.allowances
    net = gross - salary_struct.deductions

    payslip = Payslip(
        employee_id=data.employee_id,
        salary_structure_id=salary_struct.id,
        month=data.month,
        year=data.year,
        basic_salary=salary_struct.basic_salary,
        allowances=salary_struct.allowances,
        deductions=salary_struct.deductions,
        gross_salary=gross,
        net_salary=net,
    )
    db.add(payslip)
    db.commit()

    log_action(db, "payslip_generated", "payslip", payslip.id, current_user.id)
    db.refresh(payslip)
    return payslip


def get_payslips(
    db: Session,
    current_user: User,
    employee_id_param: Optional[int] = None,
) -> List[Payslip]:
    if current_user.role == "employee":
        emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")
        if employee_id_param is not None and employee_id_param != emp.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot query other employees' payslips",
            )
        return db.query(Payslip).filter(Payslip.employee_id == emp.id).all()
    else:
        if employee_id_param:
            target_emp = db.query(Employee).filter(Employee.id == employee_id_param).first()
            if not target_emp:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Employee with ID {employee_id_param} not found",
                )
            return db.query(Payslip).filter(Payslip.employee_id == employee_id_param).all()
        return db.query(Payslip).all()


def get_payslip_by_id(db: Session, current_user: User, payslip_id: int) -> Payslip:
    payslip = db.query(Payslip).filter(Payslip.id == payslip_id).first()
    if not payslip:
        raise HTTPException(status_code=404, detail="Payslip not found")

    if current_user.role == "employee":
        emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not emp or payslip.employee_id != emp.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot view another employee's payslip",
            )
    return payslip
