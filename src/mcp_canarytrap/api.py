"""FastAPI reporting API and minimal browser dashboard."""
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
import uvicorn
from .harness import DemoHarness
from .storage import Store

app = FastAPI(title="MCP-CanaryTrap", version="1.0.0",
              description="Educational deterministic decoy-access detection demo.")
store = Store()
harness = DemoHarness(store)
TEMPLATE = Path(__file__).parent / "templates" / "index.html"

@app.get("/", response_class=HTMLResponse, tags=["dashboard"])
def dashboard() -> str:
    """Serve the static dashboard HTML."""
    return TEMPLATE.read_text(encoding="utf-8")

@app.get("/health", tags=["system"])
def health() -> dict:
    """Basic liveness check."""
    return {"status": "ok", "service": "MCP-CanaryTrap", "mode": "simulation"}

@app.get("/api/sessions", tags=["sessions"])
def sessions() -> list[dict]:
    """List persisted test sessions."""
    return store.list_sessions()

@app.get("/api/events", tags=["events"])
def events(session_id: str | None = Query(default=None)) -> list[dict]:
    """List recent events, optionally filtered by session ID."""
    return store.list_events(session_id)

@app.post("/api/demo/{scenario}", tags=["demo"])
def run_demo(scenario: str) -> dict:
    """Run a benign or overreaching simulation and return evidence."""
    if scenario not in {"benign", "overreaching"}:
        raise HTTPException(status_code=400, detail="scenario must be benign or overreaching")
    return harness.run(scenario)

def run() -> None:
    """Start the local development server."""
    uvicorn.run("mcp_canarytrap.api:app", host="127.0.0.1", port=8000, reload=False)

if __name__ == "__main__":
    run()
