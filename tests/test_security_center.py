# Annotated source file for MCP-CanaryTrap v1.3.2.
# Lines beginning with "Explanation:" describe the following statement or branch.
# Original executable statements are preserved; comments are for learning.

# Explanation: Imports modules that this file uses.
import json
# Explanation: Imports names from fastapi.testclient.
from fastapi.testclient import TestClient

# Explanation: Imports names from mcp_canarytrap.
from mcp_canarytrap import api
# Explanation: Imports names from mcp_canarytrap.security_center.
from mcp_canarytrap.security_center import policy_decision, resolve_gateway_tenant


# Explanation: Function setup_env: implements the operation described by its name and body.
def setup_env(monkeypatch, tmp_path):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setenv("CANARYTRAP_DB", str(tmp_path / "security.sqlite3"))
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setenv("CANARYTRAP_RBAC_KEYS", "")
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setenv("APP_ENV", "development")
    # Explanation: Return this result to the caller; this ends the current function path.
    return TestClient(api.app)


# Explanation: Function test_policy_create_enforces_deny_and_is_audited: implements the operation described by its name and body.
def test_policy_create_enforces_deny_and_is_audited(monkeypatch, tmp_path):
    # Explanation: Assigns or updates a value used later by this function or module.
    client=setup_env(monkeypatch,tmp_path)
    # Explanation: Assigns or updates a value used later by this function or module.
    res=client.post("/api/security/policies",json={"name":"Block secrets","operation":"resources/read","target_pattern":"canarytrap://secret/*","action":"deny"})
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert res.status_code==200
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert policy_decision("resources/read","canarytrap://secret/payroll","resource")["action"]=="deny"
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert policy_decision("resources/read","public://docs","resource")["action"]=="allow"
    # Explanation: Assigns or updates a value used later by this function or module.
    verify=client.get("/api/security/audit/verify")
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert verify.status_code==200 and verify.json()["verified"] is True


# Explanation: Function test_inventory_posture_and_reconcile: implements the operation described by its name and body.
def test_inventory_posture_and_reconcile(monkeypatch,tmp_path):
    # Explanation: Assigns or updates a value used later by this function or module.
    client=setup_env(monkeypatch,tmp_path)
    # Explanation: Assigns or updates a value used later by this function or module.
    res=client.post("/api/security/inventory",json={"server_id":"docs","name":"Docs MCP","transport":"http","endpoint":"https://mcp.example.com/mcp","expected":True})
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert res.status_code==200
    # Explanation: Assigns or updates a value used later by this function or module.
    inventory=client.get("/api/security/inventory")
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert inventory.status_code==200 and inventory.json()[0]["server_id"]=="docs"
    # Explanation: Assigns or updates a value used later by this function or module.
    posture=client.post("/api/security/posture/scan")
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert posture.status_code==200 and "checks" in posture.json()
    # Explanation: Assigns or updates a value used later by this function or module.
    reconcile=client.post("/api/security/inventory/reconcile")
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert reconcile.status_code==200 and "unregistered_connections" in reconcile.json()


# Explanation: Function test_audit_verification_detects_tampering: implements the operation described by its name and body.
def test_audit_verification_detects_tampering(monkeypatch,tmp_path):
    # Explanation: Assigns or updates a value used later by this function or module.
    client=setup_env(monkeypatch,tmp_path)
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert client.post("/api/security/policies",json={"name":"Block admin","operation":"tools/call","target_pattern":"admin*","action":"deny"}).status_code==200
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert client.get("/api/security/audit/verify").json()["verified"] is True
    # Explanation: Imports modules that this file uses.
    import sqlite3
    # Explanation: Assigns or updates a value used later by this function or module.
    db=sqlite3.connect(str(tmp_path/"security.sqlite3"))
    # Explanation: Assigns or updates a value used later by this function or module.
    db.execute("UPDATE ct_audit SET action='tampered' WHERE sequence=1")
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    db.commit();db.close()
    # Explanation: Assigns or updates a value used later by this function or module.
    result=client.get("/api/security/audit/verify").json()
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert result["verified"] is False and result["first_invalid_sequence"]==1


# Explanation: Function test_rbac_tenant_isolation_and_viewer_cannot_write: implements the operation described by its name and body.
def test_rbac_tenant_isolation_and_viewer_cannot_write(monkeypatch,tmp_path):
    # Explanation: Assigns or updates a value used later by this function or module.
    client=setup_env(monkeypatch,tmp_path)
    # Explanation: Assigns or updates a value used later by this function or module.
    keys={"admin-a":{"role":"admin","tenant":"alpha"},"viewer-b":{"role":"viewer","tenant":"beta"}}
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setenv("CANARYTRAP_RBAC_KEYS",json.dumps(keys))
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert client.post("/api/security/policies",headers={"X-CanaryTrap-API-Key":"admin-a"},json={"name":"Alpha rule","operation":"*","target_pattern":"secret*","action":"deny"}).status_code==200
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert client.get("/api/security/policies",headers={"X-CanaryTrap-API-Key":"viewer-b"}).json()==[]
    # Explanation: Assigns or updates a value used later by this function or module.
    forbidden=client.post("/api/security/policies",headers={"X-CanaryTrap-API-Key":"viewer-b"},json={"name":"Bad","operation":"*","target_pattern":"*","action":"deny"})
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert forbidden.status_code==403
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert resolve_gateway_tenant("admin-a")=="alpha"


# Explanation: Function test_invalid_http_inventory_url_rejected: implements the operation described by its name and body.
def test_invalid_http_inventory_url_rejected(monkeypatch,tmp_path):
    # Explanation: Assigns or updates a value used later by this function or module.
    client=setup_env(monkeypatch,tmp_path)
    # Explanation: Assigns or updates a value used later by this function or module.
    response=client.post("/api/security/inventory",json={"server_id":"bad","name":"Bad URL","transport":"http","endpoint":"http://user:pass@example.com/mcp"})
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert response.status_code==422


# Explanation: Function test_sessions_and_events_are_tenant_scoped: implements the operation described by its name and body.
def test_sessions_and_events_are_tenant_scoped(monkeypatch, tmp_path):
    # Explanation: Imports names from mcp_canarytrap.harness.
    from mcp_canarytrap.harness import DemoHarness
    # Explanation: Imports names from mcp_canarytrap.storage.
    from mcp_canarytrap.storage import Store
    # Explanation: Assigns or updates a value used later by this function or module.
    store=Store(tmp_path/"tenant-sessions.sqlite3")
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setattr(api,"store",store)
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setattr(api,"harness",DemoHarness(store))
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setenv("CANARYTRAP_DB",str(tmp_path/"tenant-sessions.sqlite3"))
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setenv("CANARYTRAP_RBAC_KEYS",json.dumps({
      "key-alpha":{"role":"operator","tenant":"alpha"},
      "key-beta":{"role":"operator","tenant":"beta"}
    }))
    # Explanation: Assigns or updates a value used later by this function or module.
    client=TestClient(api.app)
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert client.post("/api/demo/overreaching",headers={"X-CanaryTrap-API-Key":"key-alpha"}).status_code==200
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert client.post("/api/demo/benign",headers={"X-CanaryTrap-API-Key":"key-beta"}).status_code==200
    # Explanation: Assigns or updates a value used later by this function or module.
    alpha=client.get("/api/sessions",headers={"X-CanaryTrap-API-Key":"key-alpha"}).json()
    # Explanation: Assigns or updates a value used later by this function or module.
    beta=client.get("/api/sessions",headers={"X-CanaryTrap-API-Key":"key-beta"}).json()
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert len(alpha)==1 and alpha[0]["tenant"]=="alpha"
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert len(beta)==1 and beta[0]["tenant"]=="beta"
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert client.get("/api/events",headers={"X-CanaryTrap-API-Key":"key-alpha"}).json()
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert len(client.get("/api/events",headers={"X-CanaryTrap-API-Key":"key-beta"}).json())==2


# Explanation: Function test_private_upstream_blocked_unless_explicitly_allowed: implements the operation described by its name and body.
def test_private_upstream_blocked_unless_explicitly_allowed(monkeypatch):
    # Explanation: Imports names from mcp_canarytrap.gateway_core.
    from mcp_canarytrap.gateway_core import validate_upstream_url
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setenv("CANARYTRAP_ALLOW_PRIVATE_UPSTREAMS","false")
    # Explanation: Imports modules that this file uses.
    import pytest
    # Explanation: Acquire/manage the context resource and release it reliably on exit.
    with pytest.raises(ValueError):
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        validate_upstream_url("http://127.0.0.1:9000/mcp")
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setenv("CANARYTRAP_ALLOW_PRIVATE_UPSTREAMS","true")
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    validate_upstream_url("http://127.0.0.1:9000/mcp")


# Explanation: Function test_default_deny_is_deterministic: implements the operation described by its name and body.
def test_default_deny_is_deterministic(monkeypatch,tmp_path):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    setup_env(monkeypatch,tmp_path)
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setenv("CANARYTRAP_DEFAULT_POLICY_ACTION","deny")
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert policy_decision("tools/call","unlisted_tool","tool")["action"]=="deny"
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert policy_decision("tools/call","unlisted_tool","tool")["rule_name"]=="default-deny"


# Explanation: Function test_viewer_cannot_read_shared_gateway_configuration: implements the operation described by its name and body.
def test_viewer_cannot_read_shared_gateway_configuration(monkeypatch,tmp_path):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    setup_env(monkeypatch,tmp_path)
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setenv("CANARYTRAP_HTTP_UPSTREAMS",json.dumps({"docs":{"url":"https://mcp.example.com/mcp","decoy_tools":["ct_decoy"]}}))
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setenv("CANARYTRAP_RBAC_KEYS",json.dumps({"read-only":{"role":"viewer","tenant":"alpha"}}))
    # Explanation: Assigns or updates a value used later by this function or module.
    response=TestClient(api.app).get("/api/gateway/config",headers={"X-CanaryTrap-API-Key":"read-only"})
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert response.status_code==403
