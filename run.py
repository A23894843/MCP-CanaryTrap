"""MCP-CanaryTrap launcher for local and Render deployment."""
import os
from pathlib import Path
import uvicorn

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
