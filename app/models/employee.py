from datetime import date
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.department import Department
    from app.models.attendance import Attendance
    from app.models.leave import LeaveRequest
    from app.models.payroll import SalaryStructure, Payslip


class Employee(Base):
    __tablename__ = "employee"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), unique=True, nullable=False, index=True
    )
    department_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("department.id"), nullable=True, index=True
    )
    manager_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("employee.id"), nullable=True, index=True
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    job_title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    joining_date: Mapped[date] = mapped_column(Date, nullable=False)
    profile_picture: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="employee")
    department: Mapped[Optional["Department"]] = relationship(
        "Department", foreign_keys=[department_id], back_populates="employees"
    )

    @property
    def department_name(self) -> Optional[str]:
        return self.department.name if self.department else None
    manager: Mapped[Optional["Employee"]] = relationship(
        "Employee", remote_side=[id], foreign_keys=[manager_id], back_populates="subordinates"
    )
    subordinates: Mapped[List["Employee"]] = relationship(
        "Employee", foreign_keys=[manager_id], back_populates="manager"
    )
    attendance_records: Mapped[List["Attendance"]] = relationship(
        "Attendance", back_populates="employee"
    )
    leave_requests: Mapped[List["LeaveRequest"]] = relationship(
        "LeaveRequest", foreign_keys="LeaveRequest.employee_id", back_populates="employee"
    )
    salary_structures: Mapped[List["SalaryStructure"]] = relationship(
        "SalaryStructure", back_populates="employee"
    )
    payslips: Mapped[List["Payslip"]] = relationship(
        "Payslip", back_populates="employee"
    )
