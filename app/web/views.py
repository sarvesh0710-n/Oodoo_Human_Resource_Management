# ==============================================================================
# TEMPLATE ROUTER - COMMENTED OUT PER USER DIRECTIVE
# Pure API + React SPA frontend is used exclusively.
# Jinja2 HTML Template rendering routes are disabled.
# ==============================================================================

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["web_ui"])

# @router.get("/", response_class=HTMLResponse)
# def index(request: Request, token: str = Depends(get_token_from_request)):
#     if token:
#         payload = decode_token(token)
#         role = payload.get("role", "employee")
#         return RedirectResponse(url=_dashboard_url_for_role(role), status_code=302)
#     return RedirectResponse(url="/login", status_code=302)
#
# @router.get("/login", response_class=HTMLResponse)
# def login_page(request: Request):
#     return templates.TemplateResponse(request=request, name="login.html")
#
# @router.get("/dashboard", response_class=HTMLResponse)
# def dashboard_page(...): ...
#
# @router.get("/attendance", response_class=HTMLResponse)
# ...
# @router.get("/leave", response_class=HTMLResponse)
# ...
# @router.get("/payroll", response_class=HTMLResponse)
# ...
# @router.get("/profile", response_class=HTMLResponse)
# ...
# @router.get("/admin-dashboard", response_class=HTMLResponse)
# ...
# @router.get("/employees-view", response_class=HTMLResponse)
# ...
# @router.get("/leave-approvals", response_class=HTMLResponse)
# ...
# @router.get("/departments", response_class=HTMLResponse)
# ...
# @router.get("/admin-payroll", response_class=HTMLResponse)
# ...

@router.get("/api/health")
def health_check():
    return JSONResponse(content={"status": "online", "mode": "react_spa_api"})
