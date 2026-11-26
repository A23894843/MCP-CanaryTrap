"""Instrumented MCP server. Keep stdout free for MCP STDIO protocol messages."""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server import MCPServer
from app.core.detector import detect_interaction
from app.storage.database import create_database, save_event

mcp = MCPServer("MCP-CanaryTrap")
create_database()

def monitor_tool(name):
    result = detect_interaction(name)
    if result["detected"]:
        save_event(result["target"], result["event_type"], result["severity"],
                   result["message"], source="mcp")
    return result

@mcp.tool()
def weather_search(city: str) -> str:
    """Return simulated weather information for a city."""
    monitor_tool("weather_search")
    return f"Simulated weather information for {city}."

@mcp.tool()
def admin_config() -> str:
    """Fictional administrator configuration decoy."""
    monitor_tool("admin_config")
    return "Fictional administrator configuration decoy."

@mcp.tool()
def customer_backup() -> str:
    """Fictional customer backup decoy."""
    monitor_tool("customer_backup")
    return "Fictional customer backup decoy."

@mcp.tool()
def system_secrets() -> str:
    """Fictional system secrets decoy."""
    monitor_tool("system_secrets")
    return "Fictional system secrets decoy."

if __name__ == "__main__":
    mcp.run()
