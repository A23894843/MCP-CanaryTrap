"""Safe simulation of the CVE-2025-6514 trust-boundary failure.

This does NOT execute shell commands or invoke a browser. It models the vulnerable
decision (untrusted endpoint accepted) and writes a harmless marker for demonstration.
"""
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

def simulate(endpoint, marker_path):
    marker = Path(marker_path).expanduser()
    marker.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "mode": "SAFE_SIMULATION_ONLY",
        "case_study": "CVE-2025-6514",
        "untrusted_authorization_endpoint": endpoint,
        "vulnerable_flow_model": "The simulated legacy flow accepts the metadata value without validation.",
        "action_taken": "No command executed. A harmless proof marker was written.",
        "marker_file": str(marker),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    marker.write_text("MCP-CanaryTrap safe simulation marker\\n", encoding="utf-8")
    return result

def main():
    parser = argparse.ArgumentParser(description="Safe CVE-2025-6514 flow simulator; no command execution.")
    parser.add_argument("--endpoint", default="file:///demo/untrusted-endpoint")
    parser.add_argument("--marker", default="/tmp/mcp-canarytrap-simulation.txt")
    args = parser.parse_args()
    print(json.dumps(simulate(args.endpoint, args.marker), indent=2))

if __name__ == "__main__":
    main()
