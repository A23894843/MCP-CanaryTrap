# Annotated source file for MCP-CanaryTrap v1.3.2.
# Lines beginning with "Explanation:" describe the following statement or branch.
# Original executable statements are preserved; comments are for learning.

# Explanation: Imports modules that this file uses.
import json

# Explanation: Imports names from fastapi.testclient.
from fastapi.testclient import TestClient

# Explanation: Imports names from mcp_canarytrap.
from mcp_canarytrap import api, gateway_core, http_gateway
# Explanation: Imports names from mcp_canarytrap.storage.
from mcp_canarytrap.storage import Store as RealStore


# Explanation: Class FakeUpstreamResponse: groups related data and operations.
class FakeUpstreamResponse:
    # Explanation: Assigns or updates a value used later by this function or module.
    status_code = 200
    # Explanation: Assigns or updates a value used later by this function or module.
    headers = {"content-type": "application/json", "mcp-session-id": "test-session"}

    # Explanation: Function __init__: implements the operation described by its name and body.
    def __init__(self, payload):
        # Explanation: Assigns or updates a value used later by this function or module.
        self.content = json.dumps(payload).encode()

    # Explanation: Async function aread: performs asynchronous work; inspect awaited calls and returned result.
    async def aread(self):
        # Explanation: Return this result to the caller; this ends the current function path.
        return self.content

    # Explanation: Async function aclose: performs asynchronous work; inspect awaited calls and returned result.
    async def aclose(self):
        # Explanation: Return this result to the caller; this ends the current function path.
        return None

    # Explanation: Async function aiter_bytes: performs asynchronous work; inspect awaited calls and returned result.
    async def aiter_bytes(self):
        # Explanation: Yields a value from a generator/stream instead of returning the whole sequence at once.
        yield self.content


# Explanation: Class FakeAsyncClient: groups related data and operations.
class FakeAsyncClient:
    # Explanation: Assigns or updates a value used later by this function or module.
    called = False
    # Explanation: Assigns or updates a value used later by this function or module.
    response_payload = {"jsonrpc": "2.0", "id": 1, "result": {"tools": [{"name": "normal_tool"}]}}

    # Explanation: Function __init__: implements the operation described by its name and body.
    def __init__(self, *args, **kwargs):
        # Explanation: Intentional no-op placeholder; this block performs no action.
        pass

    # Explanation: Async function __aenter__: performs asynchronous work; inspect awaited calls and returned result.
    async def __aenter__(self):
        # Explanation: Return this result to the caller; this ends the current function path.
        return self

    # Explanation: Async function __aexit__: performs asynchronous work; inspect awaited calls and returned result.
    async def __aexit__(self, *args):
        # Explanation: Return this result to the caller; this ends the current function path.
        return False

    # Explanation: Function build_request: implements the operation described by its name and body.
    def build_request(self, *args, **kwargs):
        # Explanation: Return this result to the caller; this ends the current function path.
        return {"args": args, "kwargs": kwargs}

    # Explanation: Async function send: performs asynchronous work; inspect awaited calls and returned result.
    async def send(self, request, stream=False):
        # Explanation: Assigns or updates a value used later by this function or module.
        type(self).called = True
        # Explanation: Return this result to the caller; this ends the current function path.
        return FakeUpstreamResponse(type(self).response_payload)

    # Explanation: Async function aclose: performs asynchronous work; inspect awaited calls and returned result.
    async def aclose(self):
        # Explanation: Return this result to the caller; this ends the current function path.
        return None


# Explanation: Function test_http_gateway_injects_decoys_in_upstream_tools_list: implements the operation described by its name and body.
def test_http_gateway_injects_decoys_in_upstream_tools_list(monkeypatch):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setenv("CANARYTRAP_HTTP_UPSTREAMS", json.dumps({"docs": {"url": "https://upstream.example/mcp", "decoy_tools": ["ct_decoy"]}}))
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setattr(http_gateway.httpx, "AsyncClient", FakeAsyncClient)
    # Explanation: Assigns or updates a value used later by this function or module.
    FakeAsyncClient.called = False
    # Explanation: Assigns or updates a value used later by this function or module.
    client = TestClient(api.app)
    # Explanation: Assigns or updates a value used later by this function or module.
    response = client.post("/gateway/docs", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert response.status_code == 200
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert FakeAsyncClient.called
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert [tool["name"] for tool in response.json()["result"]["tools"]] == ["normal_tool", "ct_decoy"]
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert response.headers["mcp-session-id"] == "test-session"


# Explanation: Function test_http_gateway_intercepts_decoy_tool_without_forwarding: implements the operation described by its name and body.
def test_http_gateway_intercepts_decoy_tool_without_forwarding(monkeypatch, tmp_path):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setenv("CANARYTRAP_DB", str(tmp_path / "gateway-events.sqlite3"))
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setenv("CANARYTRAP_HTTP_UPSTREAMS", json.dumps({"docs": {"url": "https://upstream.example/mcp", "decoy_tools": ["ct_decoy"]}}))
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setattr(http_gateway.httpx, "AsyncClient", FakeAsyncClient)
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setattr(gateway_core, "get_store", lambda: RealStore(tmp_path / "gateway-events.sqlite3"))
    # Explanation: Assigns or updates a value used later by this function or module.
    FakeAsyncClient.called = False
    # Explanation: Assigns or updates a value used later by this function or module.
    client = TestClient(api.app)
    # Explanation: Assigns or updates a value used later by this function or module.
    response = client.post("/gateway/docs", json={"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "ct_decoy", "arguments": {}}})
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert response.status_code == 200
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert not FakeAsyncClient.called
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert "ct_decoy" in response.json()["result"]["content"][0]["text"]
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert response.headers["mcp-canarytrap-event"] == "decoy-interaction-recorded"
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert RealStore(tmp_path / "gateway-events.sqlite3").list_events()[0]["is_decoy"] is True


# Explanation: Function test_sse_json_rpc_frame_gets_decoy_injection: implements the operation described by its name and body.
def test_sse_json_rpc_frame_gets_decoy_injection():
    # Explanation: Assigns or updates a value used later by this function or module.
    frame = b'data: {"jsonrpc":"2.0","id":1,"result":{"tools":[]}}'
    # Explanation: Assigns or updates a value used later by this function or module.
    transformed = http_gateway._transform_sse_frame(frame, {"decoy_tools": ["ct_decoy"]}, {"1": "tools/list"})
    # Explanation: Assigns or updates a value used later by this function or module.
    payload = json.loads(transformed.decode().split("data: ", 1)[1].strip())
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert payload["result"]["tools"][0]["name"] == "ct_decoy"


# Explanation: Function test_http_gateway_denies_matching_policy_without_forwarding: implements the operation described by its name and body.
def test_http_gateway_denies_matching_policy_without_forwarding(monkeypatch, tmp_path):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setenv("CANARYTRAP_DB", str(tmp_path / "policy-gateway.sqlite3"))
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setenv("CANARYTRAP_RBAC_KEYS", "")
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setenv("CANARYTRAP_HTTP_UPSTREAMS", json.dumps({"docs": {"url": "https://upstream.example/mcp", "decoy_tools": ["ct_decoy"]}}))
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setattr(http_gateway.httpx, "AsyncClient", FakeAsyncClient)
    # Explanation: Imports names from mcp_canarytrap.security_center.
    from mcp_canarytrap.security_center import router
    # Explanation: Assigns or updates a value used later by this function or module.
    client = TestClient(api.app)
    # Explanation: Assigns or updates a value used later by this function or module.
    rule = client.post("/api/security/policies", json={
        "name": "Deny sensitive", "operation": "tools/call",
        "target_pattern": "sensitive_*", "action": "deny"
    })
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert rule.status_code == 200
    # Explanation: Assigns or updates a value used later by this function or module.
    FakeAsyncClient.called = False
    # Explanation: Assigns or updates a value used later by this function or module.
    response = client.post("/gateway/docs", json={"jsonrpc":"2.0","id":9,"method":"tools/call","params":{"name":"sensitive_export","arguments":{}}})
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert response.status_code == 200
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert response.json()["error"]["code"] == -32001
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert response.headers["mcp-canarytrap-policy"] == "denied"
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert FakeAsyncClient.called is False
