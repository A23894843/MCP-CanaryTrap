"""Integration checks for the real MCP SDK learning server.

The MCP SDK is a declared project dependency. The module-level skip keeps the
non-MCP core unit tests runnable in minimal environments before dependencies
are installed; after installation, these integration checks run normally.
"""
import pytest

try:
    from mcp import Client
    from mcp_canarytrap.server import mcp
except ImportError as exc:  # Skip only this SDK integration module if not installed.
    pytest.skip(f"MCP SDK integration dependency unavailable: {exc}", allow_module_level=True)

@pytest.mark.anyio
async def test_mcp_server_exposes_expected_primitives():
    """Verify the real local MCP demo server exposes its declared primitives."""
    async with Client(mcp) as client:
        tools = await client.list_tools()
        resources = await client.list_resources()
        templates = await client.list_resource_templates()
        prompts = await client.list_prompts()
        assert {t.name for t in tools.tools} == {"search_employee", "list_departments"}
        assert {str(r.uri) for r in resources.resources} == {"company://departments"}
        assert {str(t.uri_template) for t in templates.resource_templates} == {"employee://profile/{employee_id}"}
        assert {p.name for p in prompts.prompts} == {"find_employee"}
        result = await client.call_tool("search_employee", {"employee_id": "1024"})
        assert result.is_error is False
        resource = await client.read_resource("employee://profile/1024")
        assert "Engineering" in resource.contents[0].text
