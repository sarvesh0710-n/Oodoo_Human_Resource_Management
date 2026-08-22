from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.user import User


class LeaveType(Base):
    __tablename__ = "leave_type"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    leave_requests: Mapped[List["LeaveRequest"]] = relationship(
        "LeaveRequest", back_populates="leave_type"
    )


class LeaveRequest(Base):
    __tablename__ = "leave_request"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("employee.id"), nullable=False, index=True
    )
    leave_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("leave_type.id"), nullable=False
    )
    reviewed_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("user.id"), nullable=True
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    remarks: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    review_comment: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    employee: Mapped["Employee"] = relationship(
        "Employee", foreign_keys=[employee_id], back_populates="leave_requests"
    )
    leave_type: Mapped["LeaveType"] = relationship(
        "LeaveType", back_populates="leave_requests"
    )
    reviewer: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[reviewed_by], back_populates="reviewed_leaves"
    )
