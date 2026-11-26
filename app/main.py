from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.routes import router
from app.storage.database import create_database

ROOT = Path(__file__).resolve().parent.parent
create_database()

app = FastAPI(
    title="MCP-CanaryTrap",
    description="Deterministic MCP decoy detection with a CVE-2026-5029 gateway-control prototype and verifiable evidence.",
    version="2.0.0",
)
app.include_router(router)
app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")

def page(name: str):
    return FileResponse(ROOT / "templates" / name)

@app.get("/", include_in_schema=False)
def home():
    return page("index.html")

@app.get("/dashboard", include_in_schema=False)
def dashboard():
    return page("dashboard.html")

@app.get("/decoy-lab", include_in_schema=False)
def decoy_lab():
    return page("decoy-lab.html")

@app.get("/cve-protection", include_in_schema=False)
def cve_protection():
    return page("cve-protection.html")

@app.get("/evidence", include_in_schema=False)
def evidence():
    return page("evidence.html")

@app.get("/health")
def health():
    return {"status": "ok", "application": "MCP-CanaryTrap", "version": "2.0.0"}
