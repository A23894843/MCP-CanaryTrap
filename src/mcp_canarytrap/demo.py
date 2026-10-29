# Annotated source file for MCP-CanaryTrap v1.3.2.
# Lines beginning with "Explanation:" describe the following statement or branch.
# Original executable statements are preserved; comments are for learning.

# Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
"""Command-line demonstration for both the CLEAN and FLAGGED paths."""
# Explanation: Imports modules that this file uses.
import argparse
# Explanation: Imports modules that this file uses.
import json
# Explanation: Imports names from harness.
from .harness import DemoHarness
# Explanation: Imports names from storage.
from .storage import Store

# Explanation: Function main: Parse arguments and run one deterministic demonstration scenario.
def main() -> None:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Parse arguments and run one deterministic demonstration scenario."""
    # Explanation: Assigns or updates a value used later by this function or module.
    parser = argparse.ArgumentParser(description="Run a local MCP-CanaryTrap simulation.")
    # Explanation: Assigns or updates a value used later by this function or module.
    parser.add_argument("--scenario", choices=["benign", "overreaching", "both"], default="both")
    # Explanation: Assigns or updates a value used later by this function or module.
    parser.add_argument("--db", default="canarytrap.sqlite3", help="SQLite database path")
    # Explanation: Assigns or updates a value used later by this function or module.
    args = parser.parse_args()
    # Explanation: Assigns or updates a value used later by this function or module.
    harness = DemoHarness(Store(args.db))
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    scenarios = ["benign", "overreaching"] if args.scenario == "both" else [args.scenario]
    # Explanation: Loop over each item in the iterable and run the indented body.
    for scenario in scenarios:
        # Explanation: Assigns or updates a value used later by this function or module.
        result = harness.run(scenario)
        # Explanation: Assigns or updates a value used later by this function or module.
        print(json.dumps(result, indent=2))

# Explanation: Conditional decision: execute the following branch only when this expression is true.
if __name__ == "__main__":
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    main()
