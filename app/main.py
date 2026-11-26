from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes import router
from app.api.integrated_routes import router as integrated_router
from app.security.proxy import router as security_router
from app.storage.database import create_database
from app.auth import router as auth_router, SESSION_SECRET, password_configured

ROOT = Path(__file__).resolve().parent.parent
create_database()
app = FastAPI(title="MCP-CanaryTrap", description="MCP security and vulnerability assessment suite", version="2.0.0")
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET, session_cookie="mcp_canarytrap_session", max_age=60*60*8, same_site="strict", https_only=False)
app.include_router(auth_router)
app.include_router(router)
app.include_router(security_router)
app.include_router(integrated_router)
app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")

PUBLIC_PREFIXES = ("/login", "/setup", "/auth/", "/static/")
PUBLIC_PATHS = {"/health", "/openapi.json", "/docs", "/redoc"}

@app.middleware("http")
async def require_login(request: Request, call_next):
    path = request.url.path
    if path in PUBLIC_PATHS or any(path.startswith(p) for p in PUBLIC_PREFIXES):
        return await call_next(request)
    if not password_configured():
        return RedirectResponse("/setup", status_code=303)
    if not request.session.get("authenticated"):
        if path.startswith("/api/"):
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "Authentication required"}, status_code=401)
        return RedirectResponse("/login", status_code=303)
    return await call_next(request)

@app.get("/")
def home():
    return RedirectResponse("/dashboard", status_code=303)

@app.get("/health")
def health():
    return {"status": "healthy"}

def page(name: str):
    return FileResponse(ROOT / "templates" / name)

@app.get("/dashboard", include_in_schema=False)
def dashboard(): return page("dashboard.html")
@app.get("/cve", include_in_schema=False)
def cve_page(): return page("cve.html")
@app.get("/simulation", include_in_schema=False)
def simulation_page(): return page("simulation.html")
@app.get("/auditor", include_in_schema=False)
def auditor_page(): return page("auditor.html")
@app.get("/url-validator", include_in_schema=False)
def url_validator_page(): return page("url-validator.html")
@app.get("/decoy-monitor", include_in_schema=False)
def decoy_monitor_page(): return page("decoy-monitor.html")
