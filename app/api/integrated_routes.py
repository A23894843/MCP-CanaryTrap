"""Unified API endpoints for all MCP-CanaryTrap modules."""
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.security.lab_simulator import simulate
from app.security.url_sanitizer import validate_authorization_endpoint
from app.security.vulnerability_auditor import audit_paths
from app.core.detector import detect_interaction
from app.storage.database import save_event

router = APIRouter(prefix="/api/suite", tags=["Integrated Assessment Suite"])
PROJECT_ROOT = Path(__file__).resolve().parents[2]

class SimulationRequest(BaseModel):
    authorization_endpoint: str = Field(
        default="https://untrusted.example.invalid/oauth/authorize",
        min_length=1, max_length=2048
    )

class AuditRequest(BaseModel):
    paths: list[str] = Field(default_factory=lambda: [str(PROJECT_ROOT)], max_length=20)

class URLRequest(BaseModel):
    authorization_endpoint: str = Field(min_length=1, max_length=4096)

class ToolRequest(BaseModel):
    tool_name: str = Field(min_length=1, max_length=100)

@router.get("/status")
def suite_status():
    return {
        "project": "MCP-CanaryTrap",
        "case_study": "CVE-2025-6514",
        "modules": [
            {"id": 1, "name": "Safe Vulnerable-Flow Simulation", "status": "ready"},
            {"id": 2, "name": "Local Dependency & Config Auditor", "status": "ready"},
            {"id": 3, "name": "Runtime URL Policy Validator", "status": "ready"},
            {"id": 4, "name": "MCP Decoy Monitoring", "status": "ready"},
        ],
    }

@router.post("/simulate")
def run_safe_simulation(payload: SimulationRequest):
    # Safe simulation only: no shell execution and no real exploit.
    marker = PROJECT_ROOT / "data" / "simulation-proof.txt"
    result = simulate(payload.authorization_endpoint, marker)
    result["marker_file"] = str(marker)
    return result

@router.post("/audit")
def run_local_audit(payload: AuditRequest):
    valid_paths = []
    for raw in payload.paths:
        path = Path(raw).expanduser()
        if not path.exists():
            raise HTTPException(status_code=400, detail=f"Path does not exist: {raw}")
        valid_paths.append(str(path))
    findings = audit_paths(valid_paths)
    return {
        "case_study": "CVE-2025-6514",
        "affected_range": "mcp-remote >=0.0.5 and <=0.1.15",
        "fixed_version": "0.1.16",
        "findings_count": len(findings),
        "findings": findings,
        "note": "Configuration references may not reveal the resolved package version. Check lockfiles and runtime resolution.",
    }

@router.post("/validate-url")
def validate_url(payload: URLRequest):
    return {
        "case_study": "CVE-2025-6514",
        **validate_authorization_endpoint(payload.authorization_endpoint),
    }

@router.post("/inspect-tool")
def inspect_tool(payload: ToolRequest):
    result = detect_interaction(payload.tool_name.strip())
    if result["detected"]:
        save_event(
            result["target"], result["event_type"], result["severity"],
            result["message"], source="integrated-dashboard"
        )
    return result
