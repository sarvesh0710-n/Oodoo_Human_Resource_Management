from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, get_token_from_request
from app.models.department import Department
from app.models.employee import Employee
from app.models.leave import LeaveRequest, LeaveType
from app.models.attendance import Attendance
from app.models.user import User

from app.core.security import decode_token

router = APIRouter(tags=["web_ui"])
templates = Jinja2Templates(directory="app/templates")


def _dashboard_url_for_role(role: str) -> str:
    return "/admin-dashboard" if role == "admin_hr" else "/dashboard"


@router.get("/", response_class=HTMLResponse)
def index(request: Request, token: str = Depends(get_token_from_request)):
    if token:
        payload = decode_token(token)
        role = payload.get("role", "employee")
        return RedirectResponse(url=_dashboard_url_for_role(role), status_code=302)
    return RedirectResponse(url="/login", status_code=302)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "employee":
        return RedirectResponse(url=_dashboard_url_for_role(current_user.role), status_code=302)
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    departments = db.query(Department).all()
    pending_leaves = db.query(LeaveRequest).filter(LeaveRequest.status == "pending").count() if current_user.role == "admin_hr" else 0
    total_employees = db.query(Employee).count()
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "user": current_user,
            "employee": employee,
            "departments": departments,
            "pending_leaves_count": pending_leaves,
            "total_employees_count": total_employees,
        },
    )


@router.get("/attendance", response_class=HTMLResponse)
def attendance_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    return templates.TemplateResponse(
        request=request,
        name="attendance.html",
        context={
            "user": current_user,
            "employee": employee,
        },
    )


@router.get("/leave", response_class=HTMLResponse)
def leave_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    leave_types = db.query(LeaveType).all()
    return templates.TemplateResponse(
        request=request,
        name="leave.html",
        context={
            "user": current_user,
            "employee": employee,
            "leave_types": leave_types,
        },
    )


@router.get("/payroll", response_class=HTMLResponse)
def payroll_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    return templates.TemplateResponse(
        request=request,
        name="payroll.html",
        context={
            "user": current_user,
            "employee": employee,
        },
    )


@router.get("/profile", response_class=HTMLResponse)
def profile_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    department = db.query(Department).filter(Department.id == employee.department_id).first() if employee and employee.department_id else None
    manager = db.query(Employee).filter(Employee.id == employee.manager_id).first() if employee and employee.manager_id else None
    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "user": current_user,
            "employee": employee,
            "department": department,
            "manager": manager,
        },
    )


@router.get("/admin-dashboard", response_class=HTMLResponse)
def admin_dashboard_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin_hr":
        return RedirectResponse(url="/dashboard", status_code=302)
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    departments = db.query(Department).all()
    total_employees = db.query(Employee).count()
    pending_leaves = db.query(LeaveRequest).filter(LeaveRequest.status == "pending").count()
    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html",
        context={
            "user": current_user,
            "employee": employee,
            "departments": departments,
            "total_employees_count": total_employees,
            "pending_leaves_count": pending_leaves,
        },
    )


@router.get("/employees-view", response_class=HTMLResponse)
def employees_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin_hr":
        return RedirectResponse(url="/dashboard", status_code=302)
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    departments = db.query(Department).all()
    all_employees = db.query(Employee).all()
    return templates.TemplateResponse(
        request=request,
        name="employees.html",
        context={
            "user": current_user,
            "employee": employee,
            "departments": departments,
            "all_employees": all_employees,
        },
    )


@router.get("/leave-approvals", response_class=HTMLResponse)
def leave_approvals_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin_hr":
        return RedirectResponse(url="/dashboard", status_code=302)
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    return templates.TemplateResponse(
        request=request,
        name="leave_approvals.html",
        context={
            "user": current_user,
            "employee": employee,
        },
    )


@router.get("/departments", response_class=HTMLResponse)
def departments_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin_hr":
        return RedirectResponse(url="/dashboard", status_code=302)
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    all_employees = db.query(Employee).all()
    return templates.TemplateResponse(
        request=request,
        name="departments.html",
        context={
            "user": current_user,
            "employee": employee,
            "all_employees": all_employees,
        },
    )


@router.get("/admin-payroll", response_class=HTMLResponse)
def admin_payroll_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin_hr":
        return RedirectResponse(url="/dashboard", status_code=302)
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    all_employees = db.query(Employee).all()
    return templates.TemplateResponse(
        request=request,
        name="admin_payroll.html",
        context={
            "user": current_user,
            "employee": employee,
            "all_employees": all_employees,
        },
    )
