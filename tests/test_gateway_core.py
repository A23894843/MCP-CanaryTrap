# Annotated source file for MCP-CanaryTrap v1.3.2.
# Lines beginning with "Explanation:" describe the following statement or branch.
# Original executable statements are preserved; comments are for learning.

# Explanation: Imports modules that this file uses.
import json

# Explanation: Imports names from mcp_canarytrap.gateway_core.
from mcp_canarytrap.gateway_core import decoy_kind, inject_decoys, load_http_upstreams, request_operation, synthetic_response, transform_response


# Explanation: Function test_injects_configured_decoys_into_mcp_list_responses: implements the operation described by its name and body.
def test_injects_configured_decoys_into_mcp_list_responses():
    # Explanation: Assigns or updates a value used later by this function or module.
    config = {
        "decoy_tools": ["canarytrap_decoy_admin"],
        "decoy_resources": ["canarytrap://finance/payroll"],
        "decoy_prompts": ["canarytrap_decoy_policy"],
    }
    # Explanation: Assigns or updates a value used later by this function or module.
    tools = inject_decoys({"id": 1, "result": {"tools": [{"name": "normal"}]} , "_canarytrap_method": "tools/list"}, config)
    # Explanation: Assigns or updates a value used later by this function or module.
    resources = inject_decoys({"id": 2, "result": {"resources": []}, "_canarytrap_method": "resources/list"}, config)
    # Explanation: Assigns or updates a value used later by this function or module.
    prompts = inject_decoys({"id": 3, "result": {"prompts": []}, "_canarytrap_method": "prompts/list"}, config)
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert [x["name"] for x in tools["result"]["tools"]] == ["normal", "canarytrap_decoy_admin"]
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert resources["result"]["resources"][0]["uri"] == "canarytrap://finance/payroll"
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert prompts["result"]["prompts"][0]["name"] == "canarytrap_decoy_policy"
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert "_canarytrap_method" not in tools


# Explanation: Function test_decoy_interaction_is_fabricated_and_does_not_need_upstream: implements the operation described by its name and body.
def test_decoy_interaction_is_fabricated_and_does_not_need_upstream():
    # Explanation: Assigns or updates a value used later by this function or module.
    request = {"jsonrpc": "2.0", "id": 8, "method": "tools/call", "params": {"name": "canarytrap_decoy_admin", "arguments": {}}}
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert request_operation(request) == ("tools/call", "canarytrap_decoy_admin", "tool")
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert decoy_kind("canarytrap_decoy_admin", {"decoy_tools": ["canarytrap_decoy_admin"]}) == "tool"
    # Explanation: Assigns or updates a value used later by this function or module.
    response = synthetic_response(request, "tool", "canarytrap_decoy_admin")
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert response["id"] == 8
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert "canarytrap_decoy_admin" in response["result"]["content"][0]["text"]
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert synthetic_response({"method": "tools/call"}, "tool", "x") is None


# Explanation: Function test_response_correlation_injects_only_for_matching_list_method: implements the operation described by its name and body.
def test_response_correlation_injects_only_for_matching_list_method():
    # Explanation: Assigns or updates a value used later by this function or module.
    result = transform_response({"jsonrpc": "2.0", "id": 7, "result": {"tools": []}}, {"7": "tools/list"}, {"decoy_tools": ["ct_decoy"]})
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert result["result"]["tools"][0]["name"] == "ct_decoy"


# Explanation: Function test_http_upstream_config_rejects_invalid_json: implements the operation described by its name and body.
def test_http_upstream_config_rejects_invalid_json(monkeypatch):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setenv("CANARYTRAP_HTTP_UPSTREAMS", "not-json")
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        load_http_upstreams()
    except ValueError as exc:
        # Explanation: Assert an expected condition; a false condition raises AssertionError.
        assert "valid JSON" in str(exc)
    else:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise AssertionError("invalid JSON config should fail closed")


# Explanation: Function test_http_upstream_config_validates_url_and_decoy_lists: implements the operation described by its name and body.
def test_http_upstream_config_validates_url_and_decoy_lists(monkeypatch):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setenv("CANARYTRAP_HTTP_UPSTREAMS", json.dumps({"docs": {"url": "https://mcp.example/mcp", "decoy_tools": ["ct_decoy"]}}))
    # Explanation: Assigns or updates a value used later by this function or module.
    cfg = load_http_upstreams()
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert cfg["docs"]["url"] == "https://mcp.example/mcp"
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert cfg["docs"]["decoy_tools"] == ["ct_decoy"]
