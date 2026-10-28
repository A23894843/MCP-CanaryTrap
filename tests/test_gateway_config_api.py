import json

from fastapi.testclient import TestClient

from mcp_canarytrap import api, gateway_core
from mcp_canarytrap.storage import Store


def test_dashboard_can_save_activate_and_list_nonsecret_gateway_config(monkeypatch, tmp_path):
    store = Store(tmp_path / "config.sqlite3")
    monkeypatch.setattr(api, "store", store)
    monkeypatch.setattr(gateway_core, "get_store", lambda: store)
    monkeypatch.setenv("CANARYTRAP_HTTP_UPSTREAMS", "{}")
    monkeypatch.setenv("TEST_UPSTREAM_SECRET", "never-return-this-secret")
    client = TestClient(api.app)
    response = client.post("/api/gateway/connections", json={
        "connection_id": "docs-test",
        "url": "https://mcp.example.com/mcp",
        "token_env": "TEST_UPSTREAM_SECRET",
        "decoy_tools": ["ct_decoy"],
        "decoy_resources": ["canarytrap://secret/payroll"],
        "decoy_prompts": [],
    })
    assert response.status_code == 200
    assert response.json()["saved"] is True
    assert response.json()["connection"]["endpoint"] == "/gateway/docs-test"
    assert "never-return-this-secret" not in response.text
    status = client.get("/api/gateway/config")
    assert status.status_code == 200
    assert status.json()["http_connections"][0]["id"] == "docs-test"
    assert status.json()["http_connections"][0]["token_configured"] is True
    assert "never-return-this-secret" not in status.text


def test_save_gateway_config_rejects_invalid_connection_id_and_missing_decoys(monkeypatch, tmp_path):
    store = Store(tmp_path / "invalid-config.sqlite3")
    monkeypatch.setattr(api, "store", store)
    monkeypatch.setattr(gateway_core, "get_store", lambda: store)
    monkeypatch.setenv("CANARYTRAP_HTTP_UPSTREAMS", "{}")
    client = TestClient(api.app)
    invalid_id = client.post("/api/gateway/connections", json={"connection_id": "bad/id", "url": "https://mcp.example.com/mcp", "decoy_tools": ["ct_decoy"]})
    assert invalid_id.status_code == 422
    no_decoys = client.post("/api/gateway/connections", json={"connection_id": "valid-id", "url": "https://mcp.example.com/mcp"})
    assert no_decoys.status_code == 422


class FakeInitializeResponse:
    status_code = 200
    headers = {"content-type": "application/json", "mcp-session-id": "temporary-session"}
    text = ""

    def json(self):
        return {"jsonrpc": "2.0", "id": "canarytrap-init-check", "result": {
            "protocolVersion": "2025-03-26", "serverInfo": {"name": "Mock MCP", "version": "1.0"}
        }}


class FakeInitializeClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, *args, **kwargs):
        return FakeInitializeResponse()

    async def delete(self, *args, **kwargs):
        return FakeInitializeResponse()


def test_connection_test_performs_initialize_handshake(monkeypatch, tmp_path):
    store = Store(tmp_path / "handshake.sqlite3")
    monkeypatch.setattr(api, "store", store)
    monkeypatch.setattr(gateway_core, "get_store", lambda: store)
    monkeypatch.setattr(api.httpx, "AsyncClient", FakeInitializeClient)
    monkeypatch.setenv("CANARYTRAP_HTTP_UPSTREAMS", "{}")
    store.save_gateway_connection({"id": "mock", "url": "https://mcp.example.com/mcp", "token_env": "", "decoy_tools": ["ct_decoy"], "decoy_resources": [], "decoy_prompts": []})
    response = TestClient(api.app).post("/api/gateway/connections/mock/test")
    assert response.status_code == 200
    assert response.json()["connected"] is True
    assert response.json()["server_name"] == "Mock MCP"
