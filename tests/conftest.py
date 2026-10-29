# Annotated source file for MCP-CanaryTrap v1.3.2.
# Lines beginning with "Explanation:" describe the following statement or branch.
# Original executable statements are preserved; comments are for learning.

# Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
"""Keep the test suite isolated from production-by-default application settings."""
# Explanation: Imports modules that this file uses.
import os

# Unit tests for APIs exercise handlers without requiring a browser login.
# Authentication-specific tests explicitly switch api.APP_ENV to production.
# Explanation: Assigns or updates a value used later by this function or module.
os.environ["APP_ENV"] = "development"
