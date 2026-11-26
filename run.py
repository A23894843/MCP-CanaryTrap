"""Single-command launcher for the complete MCP-CanaryTrap assessment suite."""
import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)

def main():
    # Keep imports and subprocesses rooted at this project directory.
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    try:
        import uvicorn
    except ImportError:
        print("Dependencies are missing. Install once with:")
        print("  python -m pip install -r requirements.txt")
        raise SystemExit(1)

    print("=" * 66)
    print(" MCP-CanaryTrap | Integrated Security & Vulnerability Assessment")
    print("=" * 66)
    print("Starting the integrated dashboard and all assessment modules...")
    print("Dashboard : http://127.0.0.1:8000/dashboard")
    print("API docs  : http://127.0.0.1:8000/docs")
    print("Stop      : Ctrl+C")
    print("-" * 66)
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)

if __name__ == "__main__":
    main()
