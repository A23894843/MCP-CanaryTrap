# Annotated source file for MCP-CanaryTrap v1.3.2.
# Lines beginning with "Explanation:" describe the following statement or branch.
# Original executable statements are preserved; comments are for learning.

# Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
"""API-level checks for the examiner custom-test endpoint."""
# Explanation: Imports names from fastapi.testclient.
from fastapi.testclient import TestClient
# Explanation: Imports names from mcp_canarytrap.
from mcp_canarytrap import api
# Explanation: Imports names from mcp_canarytrap.harness.
from mcp_canarytrap.harness import DemoHarness
# Explanation: Imports names from mcp_canarytrap.storage.
from mcp_canarytrap.storage import Store


# Explanation: Function test_custom_test_endpoint_accepts_new_scenario_and_returns_evidence: implements the operation described by its name and body.
def test_custom_test_endpoint_accepts_new_scenario_and_returns_evidence(tmp_path, monkeypatch):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setattr(api, "harness", DemoHarness(Store(tmp_path / "api-custom.sqlite3")))
    # Explanation: Assigns or updates a value used later by this function or module.
    client = TestClient(api.app)
    # Explanation: Assigns or updates a value used later by this function or module.
    response = client.post("/api/custom-test", json={
        "case_name": "Novel examiner scenario",
        "description": "A custom resource is accessed.",
        "decoy_targets": ["custom://finance/decoy-84"],
        "interactions": [
            {"operation": "tools/call", "target": "search_employee", "target_kind": "tool"},
            {"operation": "resources/read", "target": "custom://finance/decoy-84", "target_kind": "resource"},
        ],
    })
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert response.status_code == 200
    # Explanation: Assigns or updates a value used later by this function or module.
    payload = response.json()
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert payload["verdict"]["status"] == "FLAGGED"
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert [event["is_decoy"] for event in payload["events"]] == [False, True]


# Explanation: Function test_custom_test_endpoint_rejects_duplicate_decoy_targets: implements the operation described by its name and body.
def test_custom_test_endpoint_rejects_duplicate_decoy_targets(tmp_path, monkeypatch):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setattr(api, "harness", DemoHarness(Store(tmp_path / "api-duplicate.sqlite3")))
    # Explanation: Assigns or updates a value used later by this function or module.
    client = TestClient(api.app)
    # Explanation: Assigns or updates a value used later by this function or module.
    response = client.post("/api/custom-test", json={
        "case_name": "Duplicate decoys",
        "decoy_targets": ["custom://decoy", "CUSTOM://DECOY"],
        "interactions": [{"operation": "resources/read", "target": "custom://decoy", "target_kind": "resource"}],
    })
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert response.status_code == 422
