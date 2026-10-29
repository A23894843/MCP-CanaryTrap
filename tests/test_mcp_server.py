# Annotated source file for MCP-CanaryTrap v1.3.2.
# Lines beginning with "Explanation:" describe the following statement or branch.
# Original executable statements are preserved; comments are for learning.

# Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
"""Integration checks for the real MCP SDK learning server.

The MCP SDK is a declared project dependency. The module-level skip keeps the
non-MCP core unit tests runnable in minimal environments before dependencies
are installed; after installation, these integration checks run normally.
"""
# Explanation: Imports modules that this file uses.
import pytest

# Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
try:
    # Explanation: Imports names from mcp.
    from mcp import Client
    # Explanation: Imports names from mcp_canarytrap.server.
    from mcp_canarytrap.server import mcp
except ImportError as exc:  # Skip only this SDK integration module if not installed.
    # Explanation: Assigns or updates a value used later by this function or module.
    pytest.skip(f"MCP SDK integration dependency unavailable: {exc}", allow_module_level=True)

@pytest.mark.anyio
# Explanation: Async function test_mcp_server_exposes_expected_primitives: performs asynchronous work; inspect awaited calls and returned result.
async def test_mcp_server_exposes_expected_primitives():
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Verify the real local MCP demo server exposes its declared primitives."""
    # Explanation: Asynchronously manage a resource and ensure its cleanup.
    async with Client(mcp) as client:
        # Explanation: Assigns or updates a value used later by this function or module.
        tools = await client.list_tools()
        # Explanation: Assigns or updates a value used later by this function or module.
        resources = await client.list_resources()
        # Explanation: Assigns or updates a value used later by this function or module.
        templates = await client.list_resource_templates()
        # Explanation: Assigns or updates a value used later by this function or module.
        prompts = await client.list_prompts()
        # Explanation: Assert an expected condition; a false condition raises AssertionError.
        assert {t.name for t in tools.tools} == {"search_employee", "list_departments"}
        # Explanation: Assert an expected condition; a false condition raises AssertionError.
        assert {str(r.uri) for r in resources.resources} == {"company://departments"}
        # Explanation: Assert an expected condition; a false condition raises AssertionError.
        assert {str(t.uri_template) for t in templates.resource_templates} == {"employee://profile/{employee_id}"}
        # Explanation: Assert an expected condition; a false condition raises AssertionError.
        assert {p.name for p in prompts.prompts} == {"find_employee"}
        # Explanation: Assigns or updates a value used later by this function or module.
        result = await client.call_tool("search_employee", {"employee_id": "1024"})
        # Explanation: Assert an expected condition; a false condition raises AssertionError.
        assert result.is_error is False
        # Explanation: Assigns or updates a value used later by this function or module.
        resource = await client.read_resource("employee://profile/1024")
        # Explanation: Assert an expected condition; a false condition raises AssertionError.
        assert "Engineering" in resource.contents[0].text
