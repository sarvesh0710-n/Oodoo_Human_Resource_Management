from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.employee import Employee


class Department(Base):
    __tablename__ = "department"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    manager_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("employee.id", use_alter=True, name="fk_department_manager_id"), nullable=True
    )

    # Relationships
    manager: Mapped[Optional["Employee"]] = relationship(
        "Employee", foreign_keys=[manager_id]
    )
    employees: Mapped[List["Employee"]] = relationship(
        "Employee", foreign_keys="Employee.department_id", back_populates="department"
    )
