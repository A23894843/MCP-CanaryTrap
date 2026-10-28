import json

from mcp_canarytrap.gateway_core import decoy_kind, inject_decoys, load_http_upstreams, request_operation, synthetic_response, transform_response


def test_injects_configured_decoys_into_mcp_list_responses():
    config = {
        "decoy_tools": ["canarytrap_decoy_admin"],
        "decoy_resources": ["canarytrap://finance/payroll"],
        "decoy_prompts": ["canarytrap_decoy_policy"],
    }
    tools = inject_decoys({"id": 1, "result": {"tools": [{"name": "normal"}]} , "_canarytrap_method": "tools/list"}, config)
    resources = inject_decoys({"id": 2, "result": {"resources": []}, "_canarytrap_method": "resources/list"}, config)
    prompts = inject_decoys({"id": 3, "result": {"prompts": []}, "_canarytrap_method": "prompts/list"}, config)
    assert [x["name"] for x in tools["result"]["tools"]] == ["normal", "canarytrap_decoy_admin"]
    assert resources["result"]["resources"][0]["uri"] == "canarytrap://finance/payroll"
    assert prompts["result"]["prompts"][0]["name"] == "canarytrap_decoy_policy"
    assert "_canarytrap_method" not in tools


def test_decoy_interaction_is_fabricated_and_does_not_need_upstream():
    request = {"jsonrpc": "2.0", "id": 8, "method": "tools/call", "params": {"name": "canarytrap_decoy_admin", "arguments": {}}}
    assert request_operation(request) == ("tools/call", "canarytrap_decoy_admin", "tool")
    assert decoy_kind("canarytrap_decoy_admin", {"decoy_tools": ["canarytrap_decoy_admin"]}) == "tool"
    response = synthetic_response(request, "tool", "canarytrap_decoy_admin")
    assert response["id"] == 8
    assert "canarytrap_decoy_admin" in response["result"]["content"][0]["text"]
    assert synthetic_response({"method": "tools/call"}, "tool", "x") is None


def test_response_correlation_injects_only_for_matching_list_method():
    result = transform_response({"jsonrpc": "2.0", "id": 7, "result": {"tools": []}}, {"7": "tools/list"}, {"decoy_tools": ["ct_decoy"]})
    assert result["result"]["tools"][0]["name"] == "ct_decoy"


def test_http_upstream_config_rejects_invalid_json(monkeypatch):
    monkeypatch.setenv("CANARYTRAP_HTTP_UPSTREAMS", "not-json")
    try:
        load_http_upstreams()
    except ValueError as exc:
        assert "valid JSON" in str(exc)
    else:
        raise AssertionError("invalid JSON config should fail closed")


def test_http_upstream_config_validates_url_and_decoy_lists(monkeypatch):
    monkeypatch.setenv("CANARYTRAP_HTTP_UPSTREAMS", json.dumps({"docs": {"url": "https://mcp.example/mcp", "decoy_tools": ["ct_decoy"]}}))
    cfg = load_http_upstreams()
    assert cfg["docs"]["url"] == "https://mcp.example/mcp"
    assert cfg["docs"]["decoy_tools"] == ["ct_decoy"]
