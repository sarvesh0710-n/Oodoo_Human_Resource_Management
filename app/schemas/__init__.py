from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# --- Auth Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int


class LoginRequest(BaseModel):
    email: str
    password: str


class UserRead(BaseModel):
    id: int
    employee_code: str
    email: str
    role: str
    is_verified: bool
    is_active: bool

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    employee_code: str
    email: EmailStr
    password: str
    role: str = "employee"


# --- Employee Schemas ---
class EmployeeRead(BaseModel):
    id: int
    user_id: int
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    manager_id: Optional[int] = None
    first_name: str
    last_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    job_title: Optional[str] = None
    joining_date: date
    profile_picture: Optional[str] = None

    class Config:
        from_attributes = True


class EmployeeCreate(BaseModel):
    employee_code: str
    email: EmailStr
    password: str
    role: str = "employee"
    first_name: str
    last_name: str
    department_id: Optional[int] = None
    manager_id: Optional[int] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    job_title: Optional[str] = None
    joining_date: date
    profile_picture: Optional[str] = None


class EmployeeUpdateSelf(BaseModel):
    phone: Optional[str] = None
    address: Optional[str] = None
    profile_picture: Optional[str] = None


class EmployeeUpdateAdmin(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    department_id: Optional[int] = None
    manager_id: Optional[int] = None
    job_title: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    profile_picture: Optional[str] = None


# --- Attendance Schemas ---
class AttendanceCheckIn(BaseModel):
    check_in: Optional[time] = None


class AttendanceCheckOut(BaseModel):
    check_out: Optional[time] = None


class AttendanceRead(BaseModel):
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    date: date
    check_in: Optional[time] = None
    check_out: Optional[time] = None
    status: str

    class Config:
        from_attributes = True


# --- Leave Schemas ---
class LeaveTypeRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_paid: bool

    class Config:
        from_attributes = True


class LeaveRequestCreate(BaseModel):
    leave_type_id: int
    start_date: date
    end_date: date
    remarks: Optional[str] = None


class LeaveRequestReview(BaseModel):
    status: str  # approved | rejected
    review_comment: Optional[str] = None


class LeaveRequestRead(BaseModel):
    id: int
    employee_id: int
    leave_type_id: int
    reviewed_by: Optional[int] = None
    start_date: date
    end_date: date
    remarks: Optional[str] = None
    status: str
    review_comment: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Payroll Schemas ---
class SalaryStructureCreate(BaseModel):
    employee_id: int
    basic_salary: Decimal = Field(gt=0)
    allowances: Decimal = Field(default=Decimal("0.00"), ge=0)
    deductions: Decimal = Field(default=Decimal("0.00"), ge=0)
    effective_from: date


class SalaryStructureRead(BaseModel):
    id: int
    employee_id: int
    basic_salary: Decimal
    allowances: Decimal
    deductions: Decimal
    effective_from: date
    effective_to: Optional[date] = None

    class Config:
        from_attributes = True


class PayslipGenerate(BaseModel):
    employee_id: int
    month: int = Field(ge=1, le=12)
    year: int


class PayslipRead(BaseModel):
    id: int
    employee_id: int
    salary_structure_id: int
    month: int
    year: int
    basic_salary: Decimal
    allowances: Decimal
    deductions: Decimal
    gross_salary: Decimal
    net_salary: Decimal
    generated_at: datetime

    class Config:
        from_attributes = True
