import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server import MCPServer
from app.core.detector import detect_interaction
from app.storage.database import create_database, save_event
from app.core.evidence import append_evidence

mcp = MCPServer("MCP-CanaryTrap")
create_database()

def monitor_tool(tool_name: str):
    result = detect_interaction(tool_name)
    kind = "DECOY_ACCESS" if result["detected"] else "NORMAL_INTERACTION"
    save_event(tool_name, kind, result["message"])
    append_evidence(kind, tool_name, result["verdict"], {"trigger": result["trigger"]})
    return result

@mcp.tool()
def weather_search(city: str) -> str:
    """Return simulated weather information (benign demonstration tool)."""
    monitor_tool("weather_search")
    return f"Simulated weather information for {city}."

@mcp.tool()
def admin_config() -> str:
    """Fictional decoy: administrator configuration. Access is flagged."""
    monitor_tool("admin_config")
    return "DECOY: fictional administrator configuration."

@mcp.tool()
def customer_backup() -> str:
    """Fictional decoy: customer backup resource. Access is flagged."""
    monitor_tool("customer_backup")
    return "DECOY: fictional customer backup."

@mcp.tool()
def system_secrets() -> str:
    """Fictional decoy: system secrets resource. Access is flagged."""
    monitor_tool("system_secrets")
    return "DECOY: fictional system secrets."

if __name__ == "__main__":
    mcp.run()
