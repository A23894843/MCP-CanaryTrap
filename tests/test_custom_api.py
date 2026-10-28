"""API-level checks for the examiner custom-test endpoint."""
from fastapi.testclient import TestClient
from mcp_canarytrap import api
from mcp_canarytrap.harness import DemoHarness
from mcp_canarytrap.storage import Store


def test_custom_test_endpoint_accepts_new_scenario_and_returns_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "harness", DemoHarness(Store(tmp_path / "api-custom.sqlite3")))
    client = TestClient(api.app)
    response = client.post("/api/custom-test", json={
        "case_name": "Novel examiner scenario",
        "description": "A custom resource is accessed.",
        "decoy_targets": ["custom://finance/decoy-84"],
        "interactions": [
            {"operation": "tools/call", "target": "search_employee", "target_kind": "tool"},
            {"operation": "resources/read", "target": "custom://finance/decoy-84", "target_kind": "resource"},
        ],
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload["verdict"]["status"] == "FLAGGED"
    assert [event["is_decoy"] for event in payload["events"]] == [False, True]


def test_custom_test_endpoint_rejects_duplicate_decoy_targets(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "harness", DemoHarness(Store(tmp_path / "api-duplicate.sqlite3")))
    client = TestClient(api.app)
    response = client.post("/api/custom-test", json={
        "case_name": "Duplicate decoys",
        "decoy_targets": ["custom://decoy", "CUSTOM://DECOY"],
        "interactions": [{"operation": "resources/read", "target": "custom://decoy", "target_kind": "resource"}],
    })
    assert response.status_code == 422
