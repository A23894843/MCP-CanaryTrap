import json
from fastapi.testclient import TestClient

from mcp_canarytrap import api
from mcp_canarytrap.security_center import policy_decision, resolve_gateway_tenant


def setup_env(monkeypatch, tmp_path):
    monkeypatch.setenv("CANARYTRAP_DB", str(tmp_path / "security.sqlite3"))
    monkeypatch.setenv("CANARYTRAP_RBAC_KEYS", "")
    monkeypatch.setenv("APP_ENV", "development")
    return TestClient(api.app)


def test_policy_create_enforces_deny_and_is_audited(monkeypatch, tmp_path):
    client=setup_env(monkeypatch,tmp_path)
    res=client.post("/api/security/policies",json={"name":"Block secrets","operation":"resources/read","target_pattern":"canarytrap://secret/*","action":"deny"})
    assert res.status_code==200
    assert policy_decision("resources/read","canarytrap://secret/payroll","resource")["action"]=="deny"
    assert policy_decision("resources/read","public://docs","resource")["action"]=="allow"
    verify=client.get("/api/security/audit/verify")
    assert verify.status_code==200 and verify.json()["verified"] is True


def test_inventory_posture_and_reconcile(monkeypatch,tmp_path):
    client=setup_env(monkeypatch,tmp_path)
    res=client.post("/api/security/inventory",json={"server_id":"docs","name":"Docs MCP","transport":"http","endpoint":"https://mcp.example.com/mcp","expected":True})
    assert res.status_code==200
    inventory=client.get("/api/security/inventory")
    assert inventory.status_code==200 and inventory.json()[0]["server_id"]=="docs"
    posture=client.post("/api/security/posture/scan")
    assert posture.status_code==200 and "checks" in posture.json()
    reconcile=client.post("/api/security/inventory/reconcile")
    assert reconcile.status_code==200 and "unregistered_connections" in reconcile.json()


def test_audit_verification_detects_tampering(monkeypatch,tmp_path):
    client=setup_env(monkeypatch,tmp_path)
    assert client.post("/api/security/policies",json={"name":"Block admin","operation":"tools/call","target_pattern":"admin*","action":"deny"}).status_code==200
    assert client.get("/api/security/audit/verify").json()["verified"] is True
    import sqlite3
    db=sqlite3.connect(str(tmp_path/"security.sqlite3"))
    db.execute("UPDATE ct_audit SET action='tampered' WHERE sequence=1")
    db.commit();db.close()
    result=client.get("/api/security/audit/verify").json()
    assert result["verified"] is False and result["first_invalid_sequence"]==1


def test_rbac_tenant_isolation_and_viewer_cannot_write(monkeypatch,tmp_path):
    client=setup_env(monkeypatch,tmp_path)
    keys={"admin-a":{"role":"admin","tenant":"alpha"},"viewer-b":{"role":"viewer","tenant":"beta"}}
    monkeypatch.setenv("CANARYTRAP_RBAC_KEYS",json.dumps(keys))
    assert client.post("/api/security/policies",headers={"X-CanaryTrap-API-Key":"admin-a"},json={"name":"Alpha rule","operation":"*","target_pattern":"secret*","action":"deny"}).status_code==200
    assert client.get("/api/security/policies",headers={"X-CanaryTrap-API-Key":"viewer-b"}).json()==[]
    forbidden=client.post("/api/security/policies",headers={"X-CanaryTrap-API-Key":"viewer-b"},json={"name":"Bad","operation":"*","target_pattern":"*","action":"deny"})
    assert forbidden.status_code==403
    assert resolve_gateway_tenant("admin-a")=="alpha"


def test_invalid_http_inventory_url_rejected(monkeypatch,tmp_path):
    client=setup_env(monkeypatch,tmp_path)
    response=client.post("/api/security/inventory",json={"server_id":"bad","name":"Bad URL","transport":"http","endpoint":"http://user:pass@example.com/mcp"})
    assert response.status_code==422


def test_sessions_and_events_are_tenant_scoped(monkeypatch, tmp_path):
    from mcp_canarytrap.harness import DemoHarness
    from mcp_canarytrap.storage import Store
    store=Store(tmp_path/"tenant-sessions.sqlite3")
    monkeypatch.setattr(api,"store",store)
    monkeypatch.setattr(api,"harness",DemoHarness(store))
    monkeypatch.setenv("CANARYTRAP_DB",str(tmp_path/"tenant-sessions.sqlite3"))
    monkeypatch.setenv("CANARYTRAP_RBAC_KEYS",json.dumps({
      "key-alpha":{"role":"operator","tenant":"alpha"},
      "key-beta":{"role":"operator","tenant":"beta"}
    }))
    client=TestClient(api.app)
    assert client.post("/api/demo/overreaching",headers={"X-CanaryTrap-API-Key":"key-alpha"}).status_code==200
    assert client.post("/api/demo/benign",headers={"X-CanaryTrap-API-Key":"key-beta"}).status_code==200
    alpha=client.get("/api/sessions",headers={"X-CanaryTrap-API-Key":"key-alpha"}).json()
    beta=client.get("/api/sessions",headers={"X-CanaryTrap-API-Key":"key-beta"}).json()
    assert len(alpha)==1 and alpha[0]["tenant"]=="alpha"
    assert len(beta)==1 and beta[0]["tenant"]=="beta"
    assert client.get("/api/events",headers={"X-CanaryTrap-API-Key":"key-alpha"}).json()
    assert len(client.get("/api/events",headers={"X-CanaryTrap-API-Key":"key-beta"}).json())==2


def test_private_upstream_blocked_unless_explicitly_allowed(monkeypatch):
    from mcp_canarytrap.gateway_core import validate_upstream_url
    monkeypatch.setenv("CANARYTRAP_ALLOW_PRIVATE_UPSTREAMS","false")
    import pytest
    with pytest.raises(ValueError):
        validate_upstream_url("http://127.0.0.1:9000/mcp")
    monkeypatch.setenv("CANARYTRAP_ALLOW_PRIVATE_UPSTREAMS","true")
    validate_upstream_url("http://127.0.0.1:9000/mcp")


def test_default_deny_is_deterministic(monkeypatch,tmp_path):
    setup_env(monkeypatch,tmp_path)
    monkeypatch.setenv("CANARYTRAP_DEFAULT_POLICY_ACTION","deny")
    assert policy_decision("tools/call","unlisted_tool","tool")["action"]=="deny"
    assert policy_decision("tools/call","unlisted_tool","tool")["rule_name"]=="default-deny"


def test_viewer_cannot_read_shared_gateway_configuration(monkeypatch,tmp_path):
    setup_env(monkeypatch,tmp_path)
    monkeypatch.setenv("CANARYTRAP_HTTP_UPSTREAMS",json.dumps({"docs":{"url":"https://mcp.example.com/mcp","decoy_tools":["ct_decoy"]}}))
    monkeypatch.setenv("CANARYTRAP_RBAC_KEYS",json.dumps({"read-only":{"role":"viewer","tenant":"alpha"}}))
    response=TestClient(api.app).get("/api/gateway/config",headers={"X-CanaryTrap-API-Key":"read-only"})
    assert response.status_code==403
