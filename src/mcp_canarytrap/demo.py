"""Command-line demonstration for both the CLEAN and FLAGGED paths."""
import argparse
import json
from .harness import DemoHarness
from .storage import Store

def main() -> None:
    """Parse arguments and run one deterministic demonstration scenario."""
    parser = argparse.ArgumentParser(description="Run a local MCP-CanaryTrap simulation.")
    parser.add_argument("--scenario", choices=["benign", "overreaching", "both"], default="both")
    parser.add_argument("--db", default="canarytrap.sqlite3", help="SQLite database path")
    args = parser.parse_args()
    harness = DemoHarness(Store(args.db))
    scenarios = ["benign", "overreaching"] if args.scenario == "both" else [args.scenario]
    for scenario in scenarios:
        result = harness.run(scenario)
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
