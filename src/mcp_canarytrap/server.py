# Annotated source file for MCP-CanaryTrap v1.3.2.
# Lines beginning with "Explanation:" describe the following statement or branch.
# Original executable statements are preserved; comments are for learning.

# Explanation: Imports names from mcp.server.
from mcp.server import MCPServer

# Explanation: Assigns or updates a value used later by this function or module.
mcp = MCPServer(
    "CanaryTrap Phase 1 Demo",
    instructions="Educational MCP server for studying tools, resources, prompts and runtime access.",
)

# Explanation: Sets a module-level constant or configuration value.
EMPLOYEES = {
    "1024": {"name": "Aarav", "department": "Engineering"},
    "1025": {"name": "Diya", "department": "Finance"},
}

@mcp.tool()
# Explanation: Function search_employee: Find an employee's basic profile.
def search_employee(employee_id: str) -> str:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Find an employee's basic profile."""
    # Explanation: Assigns or updates a value used later by this function or module.
    employee = EMPLOYEES.get(employee_id)
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if employee is None:
        # Explanation: Return this result to the caller; this ends the current function path.
        return f"Employee {employee_id} was not found."
    # Explanation: Return this result to the caller; this ends the current function path.
    return f"{employee['name']} works in {employee['department']}."

@mcp.tool()
# Explanation: Function list_departments: List departments represented in the demo directory.
def list_departments() -> str:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """List departments represented in the demo directory."""
    # Explanation: Return this result to the caller; this ends the current function path.
    return "\n".join(sorted({e["department"] for e in EMPLOYEES.values()}))

@mcp.resource("employee://profile/{employee_id}")
# Explanation: Function employee_profile: Return a small employee profile as an MCP resource.
def employee_profile(employee_id: str) -> str:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Return a small employee profile as an MCP resource."""
    # Explanation: Assigns or updates a value used later by this function or module.
    employee = EMPLOYEES.get(employee_id)
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if employee is None:
        # Explanation: Return this result to the caller; this ends the current function path.
        return f"No profile exists for employee {employee_id}."
    # Explanation: Return this result to the caller; this ends the current function path.
    return f"employee_id: {employee_id}\nname: {employee['name']}\ndepartment: {employee['department']}"

@mcp.resource("company://departments")
# Explanation: Function company_departments: Return the department directory.
def company_departments() -> str:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Return the department directory."""
    # Explanation: Return this result to the caller; this ends the current function path.
    return "\n".join(sorted({e["department"] for e in EMPLOYEES.values()}))

@mcp.prompt()
# Explanation: Function find_employee: Create a user-selected prompt for looking up an employee.
def find_employee(employee_id: str) -> str:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Create a user-selected prompt for looking up an employee."""
    # Explanation: Return this result to the caller; this ends the current function path.
    return f"Find the basic profile and department for employee {employee_id}."

# Explanation: Conditional decision: execute the following branch only when this expression is true.
if __name__ == "__main__":
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    mcp.run()
