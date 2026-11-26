from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.api.routes import router
from app.storage.database import create_database
from app.security.proxy import router as security_router
from app.api.integrated_routes import router as integrated_router

ROOT = Path(__file__).resolve().parent.parent
create_database()
app = FastAPI(title="MCP-CanaryTrap",
              description="Rule-based monitoring for configured MCP decoy tools",
              version="1.0.0")
app.include_router(router)
app.include_router(security_router)
app.include_router(integrated_router)
app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")

@app.get("/")
def home():
    return {"application": "MCP-CanaryTrap", "status": "running",
            "dashboard": "/dashboard", "api_documentation": "/docs"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/dashboard", include_in_schema=False)
def dashboard():
    return FileResponse(ROOT / "templates" / "dashboard.html")
