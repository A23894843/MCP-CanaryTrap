import json

from fastapi.testclient import TestClient

from mcp_canarytrap import api, gateway_core, http_gateway
from mcp_canarytrap.storage import Store as RealStore


class FakeUpstreamResponse:
    status_code = 200
    headers = {"content-type": "application/json", "mcp-session-id": "test-session"}

    def __init__(self, payload):
        self.content = json.dumps(payload).encode()

    async def aread(self):
        return self.content

    async def aclose(self):
        return None

    async def aiter_bytes(self):
        yield self.content


class FakeAsyncClient:
    called = False
    response_payload = {"jsonrpc": "2.0", "id": 1, "result": {"tools": [{"name": "normal_tool"}]}}

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    def build_request(self, *args, **kwargs):
        return {"args": args, "kwargs": kwargs}

    async def send(self, request, stream=False):
        type(self).called = True
        return FakeUpstreamResponse(type(self).response_payload)

    async def aclose(self):
        return None


def test_http_gateway_injects_decoys_in_upstream_tools_list(monkeypatch):
    monkeypatch.setenv("CANARYTRAP_HTTP_UPSTREAMS", json.dumps({"docs": {"url": "https://upstream.example/mcp", "decoy_tools": ["ct_decoy"]}}))
    monkeypatch.setattr(http_gateway.httpx, "AsyncClient", FakeAsyncClient)
    FakeAsyncClient.called = False
    client = TestClient(api.app)
    response = client.post("/gateway/docs", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
    assert response.status_code == 200
    assert FakeAsyncClient.called
    assert [tool["name"] for tool in response.json()["result"]["tools"]] == ["normal_tool", "ct_decoy"]
    assert response.headers["mcp-session-id"] == "test-session"


def test_http_gateway_intercepts_decoy_tool_without_forwarding(monkeypatch, tmp_path):
    monkeypatch.setenv("CANARYTRAP_DB", str(tmp_path / "gateway-events.sqlite3"))
    monkeypatch.setenv("CANARYTRAP_HTTP_UPSTREAMS", json.dumps({"docs": {"url": "https://upstream.example/mcp", "decoy_tools": ["ct_decoy"]}}))
    monkeypatch.setattr(http_gateway.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(gateway_core, "get_store", lambda: RealStore(tmp_path / "gateway-events.sqlite3"))
    FakeAsyncClient.called = False
    client = TestClient(api.app)
    response = client.post("/gateway/docs", json={"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "ct_decoy", "arguments": {}}})
    assert response.status_code == 200
    assert not FakeAsyncClient.called
    assert "ct_decoy" in response.json()["result"]["content"][0]["text"]
    assert response.headers["mcp-canarytrap-event"] == "decoy-interaction-recorded"
    assert RealStore(tmp_path / "gateway-events.sqlite3").list_events()[0]["is_decoy"] is True


def test_sse_json_rpc_frame_gets_decoy_injection():
    frame = b'data: {"jsonrpc":"2.0","id":1,"result":{"tools":[]}}'
    transformed = http_gateway._transform_sse_frame(frame, {"decoy_tools": ["ct_decoy"]}, {"1": "tools/list"})
    payload = json.loads(transformed.decode().split("data: ", 1)[1].strip())
    assert payload["result"]["tools"][0]["name"] == "ct_decoy"


def test_http_gateway_denies_matching_policy_without_forwarding(monkeypatch, tmp_path):
    monkeypatch.setenv("CANARYTRAP_DB", str(tmp_path / "policy-gateway.sqlite3"))
    monkeypatch.setenv("CANARYTRAP_RBAC_KEYS", "")
    monkeypatch.setenv("CANARYTRAP_HTTP_UPSTREAMS", json.dumps({"docs": {"url": "https://upstream.example/mcp", "decoy_tools": ["ct_decoy"]}}))
    monkeypatch.setattr(http_gateway.httpx, "AsyncClient", FakeAsyncClient)
    from mcp_canarytrap.security_center import router
    client = TestClient(api.app)
    rule = client.post("/api/security/policies", json={
        "name": "Deny sensitive", "operation": "tools/call",
        "target_pattern": "sensitive_*", "action": "deny"
    })
    assert rule.status_code == 200
    FakeAsyncClient.called = False
    response = client.post("/gateway/docs", json={"jsonrpc":"2.0","id":9,"method":"tools/call","params":{"name":"sensitive_export","arguments":{}}})
    assert response.status_code == 200
    assert response.json()["error"]["code"] == -32001
    assert response.headers["mcp-canarytrap-policy"] == "denied"
    assert FakeAsyncClient.called is False
