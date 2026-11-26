"""Instrumented MCP server. Keep stdout free for MCP STDIO protocol messages."""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server import MCPServer
from app.core.detector import detect_interaction
from app.storage.database import create_database, save_event
from app.core.decoys import get_decoys

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
    """Fictional customer backup archive decoy."""
    monitor_tool("customer_backup")
    return "Fictional customer backup archive decoy."

@mcp.tool()
def system_secrets() -> str:
    """Fictional system secrets index decoy."""
    monitor_tool("system_secrets")
    return "Fictional system secrets index decoy."

@mcp.tool()
def cloud_credentials() -> str:
    """Fictional cloud access credentials decoy."""
    monitor_tool("cloud_credentials")
    return "Fictional cloud access credentials decoy."

@mcp.tool()
def database_dump() -> str:
    """Fictional database export decoy."""
    monitor_tool("database_dump")
    return "Fictional database export decoy."

@mcp.tool()
def api_tokens() -> str:
    """Fictional API token inventory decoy."""
    monitor_tool("api_tokens")
    return "Fictional API token inventory decoy."

@mcp.tool()
def ssh_private_keys() -> str:
    """Fictional SSH private-key vault decoy."""
    monitor_tool("ssh_private_keys")
    return "Fictional SSH private-key vault decoy."

@mcp.tool()
def payroll_records() -> str:
    """Fictional payroll records decoy."""
    monitor_tool("payroll_records")
    return "Fictional payroll records decoy."

@mcp.tool()
def employee_directory() -> str:
    """Fictional internal employee directory decoy."""
    monitor_tool("employee_directory")
    return "Fictional internal employee directory decoy."

@mcp.tool()
def customer_pii() -> str:
    """Fictional customer personal-data index decoy."""
    monitor_tool("customer_pii")
    return "Fictional customer personal-data index decoy."

@mcp.tool()
def billing_records() -> str:
    """Fictional billing and invoice archive decoy."""
    monitor_tool("billing_records")
    return "Fictional billing and invoice archive decoy."

@mcp.tool()
def backup_archive() -> str:
    """Fictional infrastructure backup archive decoy."""
    monitor_tool("backup_archive")
    return "Fictional infrastructure backup archive decoy."

@mcp.tool()
def root_access() -> str:
    """Fictional privileged-access registry decoy."""
    monitor_tool("root_access")
    return "Fictional privileged-access registry decoy."

@mcp.tool()
def deployment_secrets() -> str:
    """Fictional deployment secret store decoy."""
    monitor_tool("deployment_secrets")
    return "Fictional deployment secret store decoy."

@mcp.tool()
def kubernetes_config() -> str:
    """Fictional Kubernetes cluster configuration decoy."""
    monitor_tool("kubernetes_config")
    return "Fictional Kubernetes cluster configuration decoy."

@mcp.tool()
def internal_network_map() -> str:
    """Fictional internal network topology decoy."""
    monitor_tool("internal_network_map")
    return "Fictional internal network topology decoy."

@mcp.tool()
def audit_logs() -> str:
    """Fictional security audit-log archive decoy."""
    monitor_tool("audit_logs")
    return "Fictional security audit-log archive decoy."

@mcp.tool()
def source_code_archive() -> str:
    """Fictional proprietary source-code archive decoy."""
    monitor_tool("source_code_archive")
    return "Fictional proprietary source-code archive decoy."

@mcp.tool()
def oauth_refresh_tokens() -> str:
    """Fictional OAuth refresh-token store decoy."""
    monitor_tool("oauth_refresh_tokens")
    return "Fictional OAuth refresh-token store decoy."

@mcp.tool()
def service_account_keys() -> str:
    """Fictional service-account key vault decoy."""
    monitor_tool("service_account_keys")
    return "Fictional service-account key vault decoy."

@mcp.tool()
def firewall_rules() -> str:
    """Fictional perimeter firewall policy decoy."""
    monitor_tool("firewall_rules")
    return "Fictional perimeter firewall policy decoy."

@mcp.tool()
def production_env() -> str:
    """Fictional production environment settings decoy."""
    monitor_tool("production_env")
    return "Fictional production environment settings decoy."

@mcp.tool()
def incident_reports() -> str:
    """Fictional incident-response report archive decoy."""
    monitor_tool("incident_reports")
    return "Fictional incident-response report archive decoy."

@mcp.tool()
def vpn_profiles() -> str:
    """Fictional remote-access VPN profile decoy."""
    monitor_tool("vpn_profiles")
    return "Fictional remote-access VPN profile decoy."

@mcp.tool()
def email_archive() -> str:
    """Fictional corporate email archive decoy."""
    monitor_tool("email_archive")
    return "Fictional corporate email archive decoy."

@mcp.tool()
def payment_gateway_keys() -> str:
    """Fictional payment gateway key vault decoy."""
    monitor_tool("payment_gateway_keys")
    return "Fictional payment gateway key vault decoy."

@mcp.tool()
def database_admin() -> str:
    """Fictional database administrator console decoy."""
    monitor_tool("database_admin")
    return "Fictional database administrator console decoy."

@mcp.tool()
def backup_encryption_keys() -> str:
    """Fictional backup encryption key store decoy."""
    monitor_tool("backup_encryption_keys")
    return "Fictional backup encryption key store decoy."

@mcp.tool()
def cloud_storage_buckets() -> str:
    """Fictional private cloud storage inventory decoy."""
    monitor_tool("cloud_storage_buckets")
    return "Fictional private cloud storage inventory decoy."

@mcp.tool()
def mfa_recovery_codes() -> str:
    """Fictional MFA recovery-code vault decoy."""
    monitor_tool("mfa_recovery_codes")
    return "Fictional MFA recovery-code vault decoy."

if __name__ == "__main__":
    mcp.run()
