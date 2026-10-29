# Annotated source file for MCP-CanaryTrap v1.3.2.
# Lines beginning with "Explanation:" describe the following statement or branch.
# Original executable statements are preserved; comments are for learning.

# Explanation: Imports modules that this file uses.
import json

# Explanation: Imports names from fastapi.testclient.
from fastapi.testclient import TestClient

# Explanation: Imports names from mcp_canarytrap.
from mcp_canarytrap import api, gateway_core
# Explanation: Imports names from mcp_canarytrap.storage.
from mcp_canarytrap.storage import Store


# Explanation: Function test_dashboard_can_save_activate_and_list_nonsecret_gateway_config: implements the operation described by its name and body.
def test_dashboard_can_save_activate_and_list_nonsecret_gateway_config(monkeypatch, tmp_path):
    # Explanation: Assigns or updates a value used later by this function or module.
    store = Store(tmp_path / "config.sqlite3")
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setattr(api, "store", store)
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setattr(gateway_core, "get_store", lambda: store)
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setenv("CANARYTRAP_HTTP_UPSTREAMS", "{}")
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setenv("TEST_UPSTREAM_SECRET", "never-return-this-secret")
    # Explanation: Assigns or updates a value used later by this function or module.
    client = TestClient(api.app)
    # Explanation: Assigns or updates a value used later by this function or module.
    response = client.post("/api/gateway/connections", json={
        "connection_id": "docs-test",
        "url": "https://mcp.example.com/mcp",
        "token_env": "TEST_UPSTREAM_SECRET",
        "decoy_tools": ["ct_decoy"],
        "decoy_resources": ["canarytrap://secret/payroll"],
        "decoy_prompts": [],
    })
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert response.status_code == 200
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert response.json()["saved"] is True
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert response.json()["connection"]["endpoint"] == "/gateway/docs-test"
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert "never-return-this-secret" not in response.text
    # Explanation: Assigns or updates a value used later by this function or module.
    status = client.get("/api/gateway/config")
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert status.status_code == 200
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert status.json()["http_connections"][0]["id"] == "docs-test"
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert status.json()["http_connections"][0]["token_configured"] is True
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert "never-return-this-secret" not in status.text


# Explanation: Function test_save_gateway_config_rejects_invalid_connection_id_and_missing_decoys: implements the operation described by its name and body.
def test_save_gateway_config_rejects_invalid_connection_id_and_missing_decoys(monkeypatch, tmp_path):
    # Explanation: Assigns or updates a value used later by this function or module.
    store = Store(tmp_path / "invalid-config.sqlite3")
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setattr(api, "store", store)
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setattr(gateway_core, "get_store", lambda: store)
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setenv("CANARYTRAP_HTTP_UPSTREAMS", "{}")
    # Explanation: Assigns or updates a value used later by this function or module.
    client = TestClient(api.app)
    # Explanation: Assigns or updates a value used later by this function or module.
    invalid_id = client.post("/api/gateway/connections", json={"connection_id": "bad/id", "url": "https://mcp.example.com/mcp", "decoy_tools": ["ct_decoy"]})
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert invalid_id.status_code == 422
    # Explanation: Assigns or updates a value used later by this function or module.
    no_decoys = client.post("/api/gateway/connections", json={"connection_id": "valid-id", "url": "https://mcp.example.com/mcp"})
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert no_decoys.status_code == 422


# Explanation: Class FakeInitializeResponse: groups related data and operations.
class FakeInitializeResponse:
    # Explanation: Assigns or updates a value used later by this function or module.
    status_code = 200
    # Explanation: Assigns or updates a value used later by this function or module.
    headers = {"content-type": "application/json", "mcp-session-id": "temporary-session"}
    # Explanation: Assigns or updates a value used later by this function or module.
    text = ""

    # Explanation: Function json: implements the operation described by its name and body.
    def json(self):
        # Explanation: Return this result to the caller; this ends the current function path.
        return {"jsonrpc": "2.0", "id": "canarytrap-init-check", "result": {
            "protocolVersion": "2025-03-26", "serverInfo": {"name": "Mock MCP", "version": "1.0"}
        }}


# Explanation: Class FakeInitializeClient: groups related data and operations.
class FakeInitializeClient:
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

    # Explanation: Async function post: performs asynchronous work; inspect awaited calls and returned result.
    async def post(self, *args, **kwargs):
        # Explanation: Return this result to the caller; this ends the current function path.
        return FakeInitializeResponse()

    # Explanation: Async function delete: performs asynchronous work; inspect awaited calls and returned result.
    async def delete(self, *args, **kwargs):
        # Explanation: Return this result to the caller; this ends the current function path.
        return FakeInitializeResponse()


# Explanation: Function test_connection_test_performs_initialize_handshake: implements the operation described by its name and body.
def test_connection_test_performs_initialize_handshake(monkeypatch, tmp_path):
    # Explanation: Assigns or updates a value used later by this function or module.
    store = Store(tmp_path / "handshake.sqlite3")
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setattr(api, "store", store)
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setattr(gateway_core, "get_store", lambda: store)
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setattr(api.httpx, "AsyncClient", FakeInitializeClient)
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setenv("CANARYTRAP_HTTP_UPSTREAMS", "{}")
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    store.save_gateway_connection({"id": "mock", "url": "https://mcp.example.com/mcp", "token_env": "", "decoy_tools": ["ct_decoy"], "decoy_resources": [], "decoy_prompts": []})
    # Explanation: Assigns or updates a value used later by this function or module.
    response = TestClient(api.app).post("/api/gateway/connections/mock/test")
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert response.status_code == 200
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert response.json()["connected"] is True
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert response.json()["server_name"] == "Mock MCP"
