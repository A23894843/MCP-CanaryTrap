from mcp.server import MCPServer

mcp = MCPServer(
    "CanaryTrap Phase 1 Demo",
    instructions="Educational MCP server for studying tools, resources, prompts and runtime access.",
)

EMPLOYEES = {
    "1024": {"name": "Aarav", "department": "Engineering"},
    "1025": {"name": "Diya", "department": "Finance"},
}

@mcp.tool()
def search_employee(employee_id: str) -> str:
    """Find an employee's basic profile."""
    employee = EMPLOYEES.get(employee_id)
    if employee is None:
        return f"Employee {employee_id} was not found."
    return f"{employee['name']} works in {employee['department']}."

@mcp.tool()
def list_departments() -> str:
    """List departments represented in the demo directory."""
    return "\n".join(sorted({e["department"] for e in EMPLOYEES.values()}))

@mcp.resource("employee://profile/{employee_id}")
def employee_profile(employee_id: str) -> str:
    """Return a small employee profile as an MCP resource."""
    employee = EMPLOYEES.get(employee_id)
    if employee is None:
        return f"No profile exists for employee {employee_id}."
    return f"employee_id: {employee_id}\nname: {employee['name']}\ndepartment: {employee['department']}"

@mcp.resource("company://departments")
def company_departments() -> str:
    """Return the department directory."""
    return "\n".join(sorted({e["department"] for e in EMPLOYEES.values()}))

@mcp.prompt()
def find_employee(employee_id: str) -> str:
    """Create a user-selected prompt for looking up an employee."""
    return f"Find the basic profile and department for employee {employee_id}."

if __name__ == "__main__":
    mcp.run()
