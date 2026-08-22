from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.employee import Employee


class SalaryStructure(Base):
    __tablename__ = "salary_structure"
    __table_args__ = (
        CheckConstraint("basic_salary > 0", name="check_basic_salary_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("employee.id"), nullable=False, index=True
    )
    basic_salary: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    allowances: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )
    deductions: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Relationships
    employee: Mapped["Employee"] = relationship(
        "Employee", back_populates="salary_structures"
    )
    payslips: Mapped[List["Payslip"]] = relationship(
        "Payslip", back_populates="salary_structure"
    )


class Payslip(Base):
    __tablename__ = "payslip"
    __table_args__ = (
        CheckConstraint("month BETWEEN 1 AND 12", name="check_payslip_month_range"),
        UniqueConstraint("employee_id", "month", "year", name="uq_payslip_employee_month_year"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("employee.id"), nullable=False, index=True
    )
    salary_structure_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("salary_structure.id"), nullable=False
    )
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    basic_salary: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    allowances: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    deductions: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    gross_salary: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    net_salary: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    employee: Mapped["Employee"] = relationship(
        "Employee", back_populates="payslips"
    )
    salary_structure: Mapped["SalaryStructure"] = relationship(
        "SalaryStructure", back_populates="payslips"
    )
