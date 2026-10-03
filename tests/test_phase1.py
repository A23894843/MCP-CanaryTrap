import pytest
from mcp import Client
from mcp_canarytrap.phase1_design import DecoyCategory, build_phase1_decoys, create_placement_plan
from mcp_canarytrap.server import mcp

def test_taxonomy_contains_three_required_categories():
    assert {d.category for d in build_phase1_decoys()} == {
        DecoyCategory.HIGH_PRIVILEGE_TOOL,
        DecoyCategory.SENSITIVE_DATA_ASSET,
        DecoyCategory.HIGH_VALUE_RECORD,
    }

def test_placement_reproducible_for_same_session():
    assert create_placement_plan("session-001") == create_placement_plan("session-001")

@pytest.mark.anyio
async def test_mcp_server_exposes_expected_primitives():
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
