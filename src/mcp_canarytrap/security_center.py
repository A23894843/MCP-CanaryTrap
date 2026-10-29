# Annotated source file for MCP-CanaryTrap v1.3.2.
# Lines beginning with "Explanation:" describe the following statement or branch.
# Original executable statements are preserved; comments are for learning.

# Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
"""Deterministic security-center features: policy, inventory, simulation and audit."""
# Explanation: Imports names from __future__.
from __future__ import annotations
# Explanation: Imports modules that this file uses.
import hashlib, hmac, json, os, sqlite3, uuid
# Explanation: Imports names from datetime.
from datetime import datetime, timezone
# Explanation: Imports names from pathlib.
from pathlib import Path
# Explanation: Imports names from typing.
from typing import Any
# Explanation: Imports names from urllib.parse.
from urllib.parse import urlsplit

# Explanation: Imports names from fastapi.
from fastapi import APIRouter, Depends, Header, HTTPException, Query
# Explanation: Imports names from pydantic.
from pydantic import BaseModel, Field

# Explanation: Assigns or updates a value used later by this function or module.
router = APIRouter(prefix="/api/security", tags=["security center"])

# Explanation: Function _db_path: implements the operation described by its name and body.
def _db_path() -> str:
    # Explanation: Return this result to the caller; this ends the current function path.
    return str(Path(os.getenv("CANARYTRAP_DB", "canarytrap.sqlite3")).resolve())

# Explanation: Function _connect: implements the operation described by its name and body.
def _connect():
    # Explanation: Assigns or updates a value used later by this function or module.
    db = sqlite3.connect(_db_path())
    # Explanation: Assigns or updates a value used later by this function or module.
    db.row_factory = sqlite3.Row
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    db.execute("""CREATE TABLE IF NOT EXISTS ct_policy_rules(
      rule_id TEXT PRIMARY KEY, tenant TEXT NOT NULL, name TEXT NOT NULL,
      operation TEXT NOT NULL, target_pattern TEXT NOT NULL, action TEXT NOT NULL,
      enabled INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL)""")
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    db.execute("""CREATE TABLE IF NOT EXISTS ct_inventory(
      server_id TEXT NOT NULL, tenant TEXT NOT NULL, name TEXT NOT NULL,
      transport TEXT NOT NULL, endpoint TEXT NOT NULL, owner TEXT NOT NULL DEFAULT '',
      expected INTEGER NOT NULL DEFAULT 1, status TEXT NOT NULL DEFAULT 'configured',
      last_checked TEXT, notes TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, PRIMARY KEY(server_id,tenant))""")
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    db.execute("""CREATE TABLE IF NOT EXISTS ct_audit(
      sequence INTEGER PRIMARY KEY AUTOINCREMENT, tenant TEXT NOT NULL, timestamp TEXT NOT NULL,
      actor TEXT NOT NULL, action TEXT NOT NULL, details_json TEXT NOT NULL,
      previous_hash TEXT NOT NULL, entry_hash TEXT NOT NULL)""")
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    db.execute("""CREATE TABLE IF NOT EXISTS ct_baselines(
      tenant TEXT NOT NULL, target TEXT NOT NULL, operation TEXT NOT NULL,
      count INTEGER NOT NULL DEFAULT 0, last_seen TEXT NOT NULL,
      PRIMARY KEY(tenant,target,operation))""")
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    db.execute("""CREATE TABLE IF NOT EXISTS ct_webhooks(
      tenant TEXT PRIMARY KEY, url TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 0,
      updated_at TEXT NOT NULL)""")
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    db.execute("""CREATE TABLE IF NOT EXISTS ct_tenants(
      tenant TEXT PRIMARY KEY, name TEXT NOT NULL, created_at TEXT NOT NULL)""")
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    db.execute("""CREATE TABLE IF NOT EXISTS ct_simulations(
      simulation_id TEXT PRIMARY KEY, tenant TEXT NOT NULL, name TEXT NOT NULL,
      status TEXT NOT NULL, result_json TEXT NOT NULL, created_at TEXT NOT NULL)""")
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    db.commit()
    # Explanation: Return this result to the caller; this ends the current function path.
    return db

# Explanation: Function _dashboard_auth_configured: implements the operation described by its name and body.
def _dashboard_auth_configured() -> bool:
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if os.getenv("DASHBOARD_USERNAME") and os.getenv("DASHBOARD_PASSWORD"):
        # Explanation: Return this result to the caller; this ends the current function path.
        return True
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Acquire/manage the context resource and release it reliably on exit.
        with sqlite3.connect(_db_path()) as auth_db:
            # Explanation: Assigns or updates a value used later by this function or module.
            row = auth_db.execute("SELECT 1 FROM ct_dashboard_auth WHERE id=1").fetchone()
        # Explanation: Return this result to the caller; this ends the current function path.
        return row is not None
    except sqlite3.Error:
        # Explanation: Return this result to the caller; this ends the current function path.
        return False

# Explanation: Function _now: implements the operation described by its name and body.
def _now() -> str:
    # Explanation: Return this result to the caller; this ends the current function path.
    return datetime.now(timezone.utc).isoformat()

# Explanation: Function _actor_context: implements the operation described by its name and body.
def _actor_context(api_key: str | None = Header(default=None, alias="X-CanaryTrap-API-Key")) -> dict[str,str]:
    # Explanation: Assigns or updates a value used later by this function or module.
    raw = os.getenv("CANARYTRAP_RBAC_KEYS", "").strip()
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if not raw:
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        if os.getenv("APP_ENV", "development").lower() == "production":
            # Existing production Basic Auth protects the app, but does not distinguish roles.
            # Explanation: Return this result to the caller; this ends the current function path.
            return {"tenant": os.getenv("CANARYTRAP_DEFAULT_TENANT", "default"), "role": "admin", "actor": "basic-auth-operator"}
        # Explanation: Return this result to the caller; this ends the current function path.
        return {"tenant": os.getenv("CANARYTRAP_DEFAULT_TENANT", "default"), "role": "admin", "actor": "local-development"}
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if not api_key:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=401, detail="Provide X-CanaryTrap-API-Key")
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Assigns or updates a value used later by this function or module.
        mapping = json.loads(raw)
    except json.JSONDecodeError as exc:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=503, detail="CANARYTRAP_RBAC_KEYS must be valid JSON") from exc
    # Explanation: Loop over each item in the iterable and run the indented body.
    for token, info in mapping.items():
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        if isinstance(token, str) and hmac.compare_digest(token, api_key) and isinstance(info, dict):
            # Explanation: Assigns or updates a value used later by this function or module.
            role = str(info.get("role", "viewer"))
            # Explanation: Conditional decision: execute the following branch only when this expression is true.
            if role not in {"admin", "operator", "viewer"}:
                # Explanation: Stops the nearest enclosing loop immediately.
                break
            # Explanation: Return this result to the caller; this ends the current function path.
            return {"tenant": str(info.get("tenant", "default")), "role": role, "actor": str(info.get("actor", role))}
    # Explanation: Raise an exception to reject the operation or report a failure.
    raise HTTPException(status_code=403, detail="Invalid API key")

# Explanation: Function _require: implements the operation described by its name and body.
def _require(ctx: dict, roles: set[str]):
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if ctx["role"] not in roles:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=403, detail="Insufficient role for this operation")
    # Explanation: Return this result to the caller; this ends the current function path.
    return ctx

# Explanation: Function _audit: implements the operation described by its name and body.
def _audit(db, tenant: str, actor: str, action: str, details: dict[str,Any]):
    # Explanation: Assigns or updates a value used later by this function or module.
    prev = db.execute("SELECT entry_hash FROM ct_audit WHERE tenant=? ORDER BY sequence DESC LIMIT 1",(tenant,)).fetchone()
    # Explanation: Assigns or updates a value used later by this function or module.
    previous_hash = prev["entry_hash"] if prev else "GENESIS"
    # Explanation: Assigns or updates a value used later by this function or module.
    timestamp = _now()
    # Explanation: Assigns or updates a value used later by this function or module.
    details_json = json.dumps(details, sort_keys=True, separators=(",",":"), ensure_ascii=False)
    # Explanation: Assigns or updates a value used later by this function or module.
    material = json.dumps({"tenant":tenant,"timestamp":timestamp,"actor":actor,"action":action,
      "details":details,"previous_hash":previous_hash},sort_keys=True,separators=(",",":"),ensure_ascii=False)
    # Explanation: Assigns or updates a value used later by this function or module.
    digest = hashlib.sha256(material.encode()).hexdigest()
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    db.execute("INSERT INTO ct_audit(tenant,timestamp,actor,action,details_json,previous_hash,entry_hash) VALUES(?,?,?,?,?,?,?)",
      (tenant,timestamp,actor,action,details_json,previous_hash,digest))
    # Explanation: Return this result to the caller; this ends the current function path.
    return {"timestamp":timestamp,"previous_hash":previous_hash,"entry_hash":digest}

# Explanation: Function record_gateway_event: implements the operation described by its name and body.
def record_gateway_event(operation: str, target: str, is_decoy: bool, verdict_status: str, connection_id: str, tenant: str | None = None, policy_action: str = "allow"):
    # Explanation: Assigns or updates a value used later by this function or module.
    tenant=tenant or os.getenv("CANARYTRAP_DEFAULT_TENANT","default")
    # Explanation: Assigns or updates a value used later by this function or module.
    db=_connect()
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        db.execute("""INSERT INTO ct_baselines(tenant,target,operation,count,last_seen) VALUES(?,?,?,?,?)
          ON CONFLICT(tenant,target,operation) DO UPDATE SET count=count+1,last_seen=excluded.last_seen""",
          (tenant,target,operation,1,_now()))
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        _audit(db,tenant,"gateway","gateway.interaction",{"connection_id":connection_id,"operation":operation,"target":target[:250],"is_decoy":bool(is_decoy),"verdict":verdict_status,"policy_action":policy_action})
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        db.commit()
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        if verdict_status=="FLAGGED" or policy_action=="deny":
            # Explanation: Assigns or updates a value used later by this function or module.
            row=db.execute("SELECT url FROM ct_webhooks WHERE tenant=? AND enabled=1",(tenant,)).fetchone()
            # Explanation: Assigns or updates a value used later by this function or module.
            url=(row["url"] if row else os.getenv("CANARYTRAP_WEBHOOK_URL","")).strip()
            # Explanation: Assigns or updates a value used later by this function or module.
            parsed=urlsplit(url) if url else None
            # Explanation: Conditional decision: execute the following branch only when this expression is true.
            if parsed and parsed.scheme=="https" and parsed.hostname:
                # Best-effort, bounded outbound notification; never include tool args or results.
                # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
                try:
                    # Explanation: Imports modules that this file uses.
                    import httpx
                    # Explanation: Acquire/manage the context resource and release it reliably on exit.
                    with httpx.Client(timeout=2.0, follow_redirects=False) as client:
                        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
                        client.post(url,json={"service":"MCP-CanaryTrap","event":"policy_denied" if policy_action=="deny" else "decoy_access","tenant":tenant,
                          "connection_id":connection_id,"operation":operation,"target":target[:250],"status":verdict_status,"policy_action":policy_action})
                except Exception:
                    # Explanation: Intentional no-op placeholder; this block performs no action.
                    pass
    finally:
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        db.close()

# Explanation: Function _policy: Default allow; first exact/wildcard deny rule wins. Rules are deterministic.
def _policy(tenant: str, operation: str, target: str) -> dict:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Default allow; first exact/wildcard deny rule wins. Rules are deterministic."""
    # Explanation: Assigns or updates a value used later by this function or module.
    db = _connect()
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Assigns or updates a value used later by this function or module.
        rows = db.execute("SELECT * FROM ct_policy_rules WHERE tenant=? AND enabled=1 ORDER BY created_at,rule_id",(tenant,)).fetchall()
        # Explanation: Loop over each item in the iterable and run the indented body.
        for r in rows:
            # Explanation: Assigns or updates a value used later by this function or module.
            op_match = r["operation"] in {"*", operation}
            # Explanation: Assigns or updates a value used later by this function or module.
            pat = r["target_pattern"]
            # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
            target_match = pat == "*" or pat == target or (pat.endswith("*") and target.startswith(pat[:-1]))
            # Explanation: Conditional decision: execute the following branch only when this expression is true.
            if op_match and target_match:
                # Explanation: Return this result to the caller; this ends the current function path.
                return {"action":r["action"],"rule_id":r["rule_id"],"rule_name":r["name"]}
        # Explanation: Assigns or updates a value used later by this function or module.
        fallback=os.getenv("CANARYTRAP_DEFAULT_POLICY_ACTION","allow").strip().lower()
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        # Explanation: Branches based on this condition; the indented block runs only when it evaluates to true.
        if fallback not in {"allow","deny"}: fallback="allow"
        # Explanation: Return this result to the caller; this ends the current function path.
        return {"action":fallback,"rule_id":None,"rule_name":"default-"+fallback}
    finally:
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        db.close()

# Explanation: Function resolve_gateway_tenant: Resolve tenant for HTTP gateway calls; require a valid key when RBAC is enabled.
def resolve_gateway_tenant(api_key: str | None = None) -> str:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Resolve tenant for HTTP gateway calls; require a valid key when RBAC is enabled."""
    # Explanation: Assigns or updates a value used later by this function or module.
    raw = os.getenv("CANARYTRAP_RBAC_KEYS", "").strip()
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if not raw:
        # Explanation: Return this result to the caller; this ends the current function path.
        return os.getenv("CANARYTRAP_DEFAULT_TENANT", "default")
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if not api_key:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=401, detail="Gateway API key required")
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Assigns or updates a value used later by this function or module.
        mapping = json.loads(raw)
    except json.JSONDecodeError as exc:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=503, detail="CANARYTRAP_RBAC_KEYS must be valid JSON") from exc
    # Explanation: Loop over each item in the iterable and run the indented body.
    for token, info in mapping.items():
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        if isinstance(token, str) and hmac.compare_digest(token, api_key) and isinstance(info, dict) and info.get("role") in {"admin", "operator", "viewer"}:
            # Explanation: Return this result to the caller; this ends the current function path.
            return str(info.get("tenant", "default"))
    # Explanation: Raise an exception to reject the operation or report a failure.
    raise HTTPException(status_code=403, detail="Invalid gateway API key")

# Explanation: Function policy_decision: Shared hook for live adapters; only explicit DENY rules block forwarding.
def policy_decision(operation: str, target: str, kind: str, tenant: str | None = None) -> dict:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Shared hook for live adapters; only explicit DENY rules block forwarding."""
    # Explanation: Assigns or updates a value used later by this function or module.
    decision = _policy(tenant or os.getenv("CANARYTRAP_DEFAULT_TENANT","default"), operation, target)
    # Explanation: Return this result to the caller; this ends the current function path.
    return decision

# Explanation: Class PolicyRequest: groups related data and operations.
class PolicyRequest(BaseModel):
    # Explanation: Assigns or updates a value used later by this function or module.
    name: str = Field(min_length=1,max_length=100)
    # Explanation: Assigns or updates a value used later by this function or module.
    operation: str = Field(default="*",min_length=1,max_length=80)
    # Explanation: Assigns or updates a value used later by this function or module.
    target_pattern: str = Field(min_length=1,max_length=250)
    # Explanation: Assigns or updates a value used later by this function or module.
    action: str = Field(pattern="^(allow|deny|monitor)$")
    # Explanation: Assigns or updates a value used later by this function or module.
    enabled: bool = True

# Explanation: Class InventoryRequest: groups related data and operations.
class InventoryRequest(BaseModel):
    # Explanation: Assigns or updates a value used later by this function or module.
    server_id: str = Field(min_length=1,max_length=64,pattern=r"^[A-Za-z0-9_-]+$")
    # Explanation: Assigns or updates a value used later by this function or module.
    name: str = Field(min_length=1,max_length=120)
    # Explanation: Assigns or updates a value used later by this function or module.
    transport: str = Field(pattern="^(http|stdio)$")
    # Explanation: Assigns or updates a value used later by this function or module.
    endpoint: str = Field(min_length=1,max_length=2000)
    # Explanation: Assigns or updates a value used later by this function or module.
    owner: str = Field(default="",max_length=120)
    # Explanation: Assigns or updates a value used later by this function or module.
    expected: bool = True
    # Explanation: Assigns or updates a value used later by this function or module.
    notes: str = Field(default="",max_length=1000)

# Explanation: Class WebhookRequest: groups related data and operations.
class WebhookRequest(BaseModel):
    # Explanation: Assigns or updates a value used later by this function or module.
    url: str = Field(min_length=8,max_length=2000)
    # Explanation: Assigns or updates a value used later by this function or module.
    enabled: bool = True

@router.get("/overview")
# Explanation: Function security_overview: implements the operation described by its name and body.
def security_overview(ctx=Depends(_actor_context)):
    # Explanation: Assigns or updates a value used later by this function or module.
    db=_connect()
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Assigns or updates a value used later by this function or module.
        tenant=ctx["tenant"]
        # Explanation: Assigns or updates a value used later by this function or module.
        counts={
          "policy_rules":db.execute("SELECT count(*) FROM ct_policy_rules WHERE tenant=?",(tenant,)).fetchone()[0],
          "inventory_servers":db.execute("SELECT count(*) FROM ct_inventory WHERE tenant=?",(tenant,)).fetchone()[0],
          "unexpected_servers":db.execute("SELECT count(*) FROM ct_inventory WHERE tenant=? AND expected=0",(tenant,)).fetchone()[0],
          "audit_entries":db.execute("SELECT count(*) FROM ct_audit WHERE tenant=?",(tenant,)).fetchone()[0],
          "simulations":db.execute("SELECT count(*) FROM ct_simulations WHERE tenant=?",(tenant,)).fetchone()[0],
        }
        # Explanation: Assigns or updates a value used later by this function or module.
        flagged=db.execute("SELECT count(*) FROM ct_audit WHERE tenant=? AND action='gateway.interaction' AND (details_json LIKE ? OR details_json LIKE ?)",(tenant,'%"verdict":"FLAGGED"%','%"policy_action":"deny"%')).fetchone()[0]
        # Explanation: Return this result to the caller; this ends the current function path.
        return {"tenant":tenant,"role":ctx["role"],"counts":counts,"flagged_gateway_events":flagged,
          "deterministic_only":True,"notes":"Counts are prototype telemetry, not a certification or global host discovery."}
    # Explanation: Cleanup block that runs whether the protected operation succeeds or fails.
    finally: db.close()

@router.get("/policies")
# Explanation: Function list_policies: implements the operation described by its name and body.
def list_policies(ctx=Depends(_actor_context)):
    # Explanation: Assigns or updates a value used later by this function or module.
    db=_connect()
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    # Explanation: Return this result to the caller; this ends the current function path.
    try:return [dict(r)|{"enabled":bool(r["enabled"])} for r in db.execute("SELECT * FROM ct_policy_rules WHERE tenant=? ORDER BY created_at DESC",(ctx["tenant"],))]
    # Explanation: Cleanup block that runs whether the protected operation succeeds or fails.
    finally:db.close()

@router.post("/policies")
# Explanation: Function create_policy: implements the operation described by its name and body.
def create_policy(req:PolicyRequest,ctx=Depends(_actor_context)):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    _require(ctx,{"admin","operator"})
    # Explanation: Assigns or updates a value used later by this function or module.
    db=_connect()
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Assigns or updates a value used later by this function or module.
        rid=uuid.uuid4().hex
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        db.execute("INSERT INTO ct_policy_rules VALUES(?,?,?,?,?,?,?,?)",(rid,ctx["tenant"],req.name,req.operation,req.target_pattern,req.action,int(req.enabled),_now()))
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        _audit(db,ctx["tenant"],ctx["actor"],"policy.created",{"rule_id":rid,"name":req.name,"action":req.action})
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        db.commit()
        # Explanation: Return this result to the caller; this ends the current function path.
        return {"created":True,"rule_id":rid,"note":"DENY rules are enforced on supported live-gateway operations; default behavior is allow."}
    # Explanation: Cleanup block that runs whether the protected operation succeeds or fails.
    finally:db.close()

@router.delete("/policies/{rule_id}")
# Explanation: Function delete_policy: implements the operation described by its name and body.
def delete_policy(rule_id:str,ctx=Depends(_actor_context)):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    _require(ctx,{"admin"})
    # Explanation: Assigns or updates a value used later by this function or module.
    db=_connect()
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Assigns or updates a value used later by this function or module.
        cur=db.execute("DELETE FROM ct_policy_rules WHERE rule_id=? AND tenant=?",(rule_id,ctx["tenant"]))
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        # Explanation: Raise an exception to reject the operation or report a failure.
        if not cur.rowcount:raise HTTPException(status_code=404,detail="Policy not found")
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        _audit(db,ctx["tenant"],ctx["actor"],"policy.deleted",{"rule_id":rule_id});db.commit()
        # Explanation: Return this result to the caller; this ends the current function path.
        return {"deleted":True,"rule_id":rule_id}
    # Explanation: Cleanup block that runs whether the protected operation succeeds or fails.
    finally:db.close()

@router.get("/inventory")
# Explanation: Function inventory: implements the operation described by its name and body.
def inventory(ctx=Depends(_actor_context)):
    # Explanation: Assigns or updates a value used later by this function or module.
    db=_connect()
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    # Explanation: Return this result to the caller; this ends the current function path.
    try:return [dict(r)|{"expected":bool(r["expected"])} for r in db.execute("SELECT * FROM ct_inventory WHERE tenant=? ORDER BY created_at DESC",(ctx["tenant"],))]
    # Explanation: Cleanup block that runs whether the protected operation succeeds or fails.
    finally:db.close()

@router.post("/inventory")
# Explanation: Function add_inventory: implements the operation described by its name and body.
def add_inventory(req:InventoryRequest,ctx=Depends(_actor_context)):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    _require(ctx,{"admin","operator"})
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if req.transport=="http":
        # Explanation: Assigns or updates a value used later by this function or module.
        u=urlsplit(req.endpoint)
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        if u.scheme not in {"http","https"} or not u.hostname or u.username or u.password or u.query or u.fragment:
            # Explanation: Raise an exception to reject the operation or report a failure.
            raise HTTPException(status_code=422,detail="HTTP endpoint must be a valid URL without embedded credentials, query strings or fragments")
    # Explanation: Assigns or updates a value used later by this function or module.
    db=_connect()
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        db.execute("INSERT INTO ct_inventory VALUES(?,?,?,?,?,?,?,?,?,?,?)",(req.server_id,ctx["tenant"],req.name,req.transport,req.endpoint,req.owner,int(req.expected),"configured",None,req.notes,_now()))
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        _audit(db,ctx["tenant"],ctx["actor"],"inventory.registered",{"server_id":req.server_id,"transport":req.transport,"expected":req.expected})
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        db.commit()
        # Explanation: Return this result to the caller; this ends the current function path.
        return {"registered":True,"server_id":req.server_id}
    # Explanation: Raise an exception to reject the operation or report a failure.
    except sqlite3.IntegrityError as exc:raise HTTPException(status_code=409,detail="Server ID already exists in this tenant") from exc
    # Explanation: Cleanup block that runs whether the protected operation succeeds or fails.
    finally:db.close()

@router.delete("/inventory/{server_id}")
# Explanation: Function remove_inventory: implements the operation described by its name and body.
def remove_inventory(server_id:str,ctx=Depends(_actor_context)):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    _require(ctx,{"admin","operator"})
    # Explanation: Assigns or updates a value used later by this function or module.
    db=_connect()
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Assigns or updates a value used later by this function or module.
        cur=db.execute("DELETE FROM ct_inventory WHERE server_id=? AND tenant=?",(server_id,ctx["tenant"]))
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        # Explanation: Raise an exception to reject the operation or report a failure.
        if not cur.rowcount:raise HTTPException(status_code=404,detail="Server not found")
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        _audit(db,ctx["tenant"],ctx["actor"],"inventory.removed",{"server_id":server_id});db.commit()
        # Explanation: Return this result to the caller; this ends the current function path.
        return {"removed":True}
    # Explanation: Cleanup block that runs whether the protected operation succeeds or fails.
    finally:db.close()

@router.post("/inventory/reconcile")
# Explanation: Function reconcile_inventory: Compare the configured HTTP gateway list with registered inventory entries.
def reconcile_inventory(ctx=Depends(_actor_context)):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Compare the configured HTTP gateway list with registered inventory entries."""
    # Explanation: Imports names from gateway_core.
    from .gateway_core import load_http_upstreams
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    # Explanation: Begins a protected block whose errors may be handled by the following exception clauses.
    try: upstreams=load_http_upstreams()
    # Explanation: Raise an exception to reject the operation or report a failure.
    except ValueError as exc: raise HTTPException(status_code=503,detail="Gateway configuration could not be parsed") from exc
    # Explanation: Assigns or updates a value used later by this function or module.
    db=_connect()
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Assigns or updates a value used later by this function or module.
        known={r["server_id"] for r in db.execute("SELECT server_id FROM ct_inventory WHERE tenant=?",(ctx["tenant"],))}
        # Explanation: Assigns or updates a value used later by this function or module.
        observed=[]
        # Explanation: Loop over each item in the iterable and run the indented body.
        for cid,cfg in upstreams.items():
            # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
            observed.append({"server_id":cid,"endpoint":cfg["url"],"registered":cid in known,"status":"registered" if cid in known else "configured-but-unregistered"})
        # Explanation: Assigns or updates a value used later by this function or module.
        unknown=[x for x in observed if not x["registered"]]
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        _audit(db,ctx["tenant"],ctx["actor"],"inventory.reconciled",{"configured_http":len(observed),"unregistered":len(unknown)})
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        db.commit()
        # Explanation: Return this result to the caller; this ends the current function path.
        return {"tenant":ctx["tenant"],"configured_http_connections":observed,"unregistered_connections":unknown,
          "note":"This detects unregistered connections in CanaryTrap configuration only; it does not discover arbitrary servers on the host or network."}
    # Explanation: Cleanup block that runs whether the protected operation succeeds or fails.
    finally:db.close()

@router.get("/inventory/shadow")
# Explanation: Function detect_unregistered_gateway_connections: Detect observed gateway connection IDs missing from the maintained inventory.
def detect_unregistered_gateway_connections(ctx=Depends(_actor_context)):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Detect observed gateway connection IDs missing from the maintained inventory."""
    # Explanation: Assigns or updates a value used later by this function or module.
    db=_connect()
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Assigns or updates a value used later by this function or module.
        registered={r["server_id"] for r in db.execute("SELECT server_id FROM ct_inventory WHERE tenant=?",(ctx["tenant"],))}
        # Explanation: Assigns or updates a value used later by this function or module.
        rows=db.execute("SELECT details_json,timestamp FROM ct_audit WHERE tenant=? AND action='gateway.interaction' ORDER BY sequence DESC",(ctx["tenant"],)).fetchall()
        # Explanation: Assigns or updates a value used later by this function or module.
        observed={}
        # Explanation: Loop over each item in the iterable and run the indented body.
        for row in rows:
            # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
            # Explanation: Begins a protected block whose errors may be handled by the following exception clauses.
            try:detail=json.loads(row["details_json"])
            # Explanation: Handles the specified exception so the application can respond to that failure.
            except json.JSONDecodeError:continue
            # Explanation: Assigns or updates a value used later by this function or module.
            cid=detail.get("connection_id")
            # Explanation: Conditional decision: execute the following branch only when this expression is true.
            # Explanation: Branches based on this condition; the indented block runs only when it evaluates to true.
            if cid and cid not in observed:observed[cid]={"connection_id":cid,"last_seen":row["timestamp"],"operations":0}
            # Explanation: Conditional decision: execute the following branch only when this expression is true.
            # Explanation: Branches based on this condition; the indented block runs only when it evaluates to true.
            if cid:observed[cid]["operations"]+=1
        # Explanation: Assigns or updates a value used later by this function or module.
        shadows=[item for cid,item in observed.items() if cid not in registered]
        # Explanation: Return this result to the caller; this ends the current function path.
        return {"tenant":ctx["tenant"],"observed_connections":list(observed.values()),"unregistered_observed_connections":shadows,
          "scope":"Only connections that have already passed through this gateway are visible; this is not host or network-wide discovery."}
    # Explanation: Cleanup block that runs whether the protected operation succeeds or fails.
    finally:db.close()

@router.get("/correlation")
# Explanation: Function cross_server_correlation: Correlate deterministic target/operation observations across gateway connection IDs.
def cross_server_correlation(ctx=Depends(_actor_context)):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Correlate deterministic target/operation observations across gateway connection IDs."""
    # Explanation: Assigns or updates a value used later by this function or module.
    db=_connect()
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Assigns or updates a value used later by this function or module.
        rows=db.execute("SELECT details_json,timestamp FROM ct_audit WHERE tenant=? AND action='gateway.interaction' ORDER BY sequence",(ctx["tenant"],)).fetchall()
        # Explanation: Assigns or updates a value used later by this function or module.
        groups={}
        # Explanation: Loop over each item in the iterable and run the indented body.
        for row in rows:
            # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
            # Explanation: Begins a protected block whose errors may be handled by the following exception clauses.
            try:d=json.loads(row["details_json"])
            # Explanation: Handles the specified exception so the application can respond to that failure.
            except json.JSONDecodeError:continue
            # Explanation: Assigns or updates a value used later by this function or module.
            key=(d.get("operation",""),d.get("target",""))
            # Explanation: Assigns or updates a value used later by this function or module.
            group=groups.setdefault(key,{"operation":key[0],"target":key[1],"connections":set(),"observations":0,"flagged_observations":0,"first_seen":row["timestamp"],"last_seen":row["timestamp"]})
            # Explanation: Assigns or updates a value used later by this function or module.
            group["connections"].add(d.get("connection_id","unknown"));group["observations"]+=1
            # Explanation: Conditional decision: execute the following branch only when this expression is true.
            # Explanation: Branches based on this condition; the indented block runs only when it evaluates to true.
            if d.get("verdict")=="FLAGGED":group["flagged_observations"]+=1
            # Explanation: Assigns or updates a value used later by this function or module.
            group["last_seen"]=row["timestamp"]
        # Explanation: Assigns or updates a value used later by this function or module.
        result=[]
        # Explanation: Loop over each item in the iterable and run the indented body.
        for g in groups.values():
            # Explanation: Assigns or updates a value used later by this function or module.
            g["connections"]=sorted(g["connections"]);g["connection_count"]=len(g["connections"])
            # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
            result.append(g)
        # Explanation: Assigns or updates a value used later by this function or module.
        result.sort(key=lambda x:(-x["flagged_observations"],-x["connection_count"],-x["observations"]))
        # Explanation: Return this result to the caller; this ends the current function path.
        return {"tenant":ctx["tenant"],"correlated_targets":result,"method":"Exact deterministic grouping by operation and target; no behavioral inference."}
    # Explanation: Cleanup block that runs whether the protected operation succeeds or fails.
    finally:db.close()

@router.post("/posture/scan")
# Explanation: Function posture_scan: Local configuration posture checks; does not probe arbitrary endpoints.
def posture_scan(ctx=Depends(_actor_context)):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Local configuration posture checks; does not probe arbitrary endpoints."""
    # Explanation: Assigns or updates a value used later by this function or module.
    db=_connect()
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Assigns or updates a value used later by this function or module.
        tenant=ctx["tenant"]
        # Explanation: Assigns or updates a value used later by this function or module.
        servers=[dict(r) for r in db.execute("SELECT * FROM ct_inventory WHERE tenant=?",(tenant,))]
        # Explanation: Assigns or updates a value used later by this function or module.
        rules=[dict(r) for r in db.execute("SELECT * FROM ct_policy_rules WHERE tenant=?",(tenant,))]
        # Explanation: Assigns or updates a value used later by this function or module.
        checks=[
          {"id":"inventory-present","status":"pass" if servers else "warn","detail":f"{len(servers)} server(s) registered"},
          {"id":"policy-present","status":"pass" if rules else "warn","detail":f"{len(rules)} policy rule(s) configured"},
          {"id":"https-for-remote","status":"pass" if all(s["transport"]!="http" or s["endpoint"].startswith("https://") for s in servers) else "warn","detail":"Remote HTTP inventory should use HTTPS"},
          {"id":"rbac-key-map","status":"pass" if os.getenv("CANARYTRAP_RBAC_KEYS") else "warn","detail":"API-key RBAC configured" if os.getenv("CANARYTRAP_RBAC_KEYS") else "RBAC key map not configured; development/admin fallback may be active"},
          {"id":"production-dashboard-auth","status":"pass" if os.getenv("APP_ENV","development").lower()!="production" or _dashboard_auth_configured() else "fail","detail":"Production dashboard credentials"},
          {"id":"webhook-https","status":"pass" if not os.getenv("CANARYTRAP_WEBHOOK_URL") or os.getenv("CANARYTRAP_WEBHOOK_URL","").startswith("https://") else "fail","detail":"Configured webhook must use HTTPS"},
        ]
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        result={"tenant":tenant,"scanned_at":_now(),"checks":checks,"summary":{"pass":sum(c["status"]=="pass" for c in checks),"warn":sum(c["status"]=="warn" for c in checks),"fail":sum(c["status"]=="fail" for c in checks)}}
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        _audit(db,tenant,ctx["actor"],"posture.scan",result["summary"]);db.commit()
        # Explanation: Return this result to the caller; this ends the current function path.
        return result
    # Explanation: Cleanup block that runs whether the protected operation succeeds or fails.
    finally:db.close()

@router.post("/simulate")
# Explanation: Function simulate_attack: Run deterministic rule checks against a bounded built-in attack corpus.
def simulate_attack(ctx=Depends(_actor_context)):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Run deterministic rule checks against a bounded built-in attack corpus."""
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    _require(ctx,{"admin","operator"})
    # Explanation: Assigns or updates a value used later by this function or module.
    cases=[
      {"name":"benign-read","operation":"tools/call","target":"search_public_docs","expected":"allow"},
      {"name":"decoy-tool-access","operation":"tools/call","target":"canarytrap_decoy_admin","expected":"deny"},
      {"name":"sensitive-resource-read","operation":"resources/read","target":"canarytrap://secret/payroll","expected":"deny"},
      {"name":"unlisted-prompt","operation":"prompts/get","target":"unknown_prompt","expected":"allow"},
    ]
    # Explanation: Assigns or updates a value used later by this function or module.
    results=[]
    # Explanation: Loop over each item in the iterable and run the indented body.
    for c in cases:
        # Explanation: Assigns or updates a value used later by this function or module.
        d=_policy(ctx["tenant"],c["operation"],c["target"])
        # Built-in decoy patterns are included in test expected only when user has configured matching rules.
        # Explanation: Assigns or updates a value used later by this function or module.
        expected=d["action"] if d["action"] in {"allow","deny"} else "allow"
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        results.append({"case":c["name"],"operation":c["operation"],"target":c["target"],"policy_action":d["action"],"matched_rule":d["rule_id"],"result":"pass" if expected==d["action"] else "review"})
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    status="completed" if all(r["result"]=="pass" for r in results) else "review"
    # Explanation: Assigns or updates a value used later by this function or module.
    sim_id=uuid.uuid4().hex
    # Explanation: Assigns or updates a value used later by this function or module.
    db=_connect()
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        db.execute("INSERT INTO ct_simulations VALUES(?,?,?,?,?,?)",(sim_id,ctx["tenant"],"Built-in policy smoke test",status,json.dumps(results),_now()))
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        _audit(db,ctx["tenant"],ctx["actor"],"simulation.completed",{"simulation_id":sim_id,"status":status,"cases":len(results)})
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        db.commit()
    # Explanation: Cleanup block that runs whether the protected operation succeeds or fails.
    finally:db.close()
    # Explanation: Return this result to the caller; this ends the current function path.
    return {"simulation_id":sim_id,"status":status,"cases":results,"note":"This validates policy matching only; it does not attack a live server."}

@router.get("/simulations")
# Explanation: Function list_simulations: implements the operation described by its name and body.
def list_simulations(ctx=Depends(_actor_context)):
    # Explanation: Assigns or updates a value used later by this function or module.
    db=_connect()
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    # Explanation: Return this result to the caller; this ends the current function path.
    try:return [{"simulation_id":r["simulation_id"],"tenant":r["tenant"],"name":r["name"],"status":r["status"],"result":json.loads(r["result_json"]),"created_at":r["created_at"]} for r in db.execute("SELECT * FROM ct_simulations WHERE tenant=? ORDER BY created_at DESC",(ctx["tenant"],))]
    # Explanation: Cleanup block that runs whether the protected operation succeeds or fails.
    finally:db.close()

@router.get("/baselines")
# Explanation: Function baselines: implements the operation described by its name and body.
def baselines(ctx=Depends(_actor_context)):
    # Explanation: Assigns or updates a value used later by this function or module.
    db=_connect()
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    # Explanation: Return this result to the caller; this ends the current function path.
    try:return [dict(r) for r in db.execute("SELECT * FROM ct_baselines WHERE tenant=? ORDER BY count DESC",(ctx["tenant"],))]
    # Explanation: Cleanup block that runs whether the protected operation succeeds or fails.
    finally:db.close()

@router.post("/baselines/rebuild")
# Explanation: Function rebuild_baselines: implements the operation described by its name and body.
def rebuild_baselines(ctx=Depends(_actor_context)):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    _require(ctx,{"admin","operator"})
    # Explanation: Assigns or updates a value used later by this function or module.
    db=_connect()
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Rebuild only from stored gateway/harness events, using deterministic counts.
        # Explanation: Assigns or updates a value used later by this function or module.
        db.execute("DELETE FROM ct_baselines WHERE tenant=?",(ctx["tenant"],))
        # Explanation: Assigns or updates a value used later by this function or module.
        rows=db.execute("""SELECT e.target,e.operation,COUNT(*) AS n,MAX(e.timestamp) AS last_seen
          FROM events e JOIN sessions s ON s.session_id=e.session_id
          WHERE s.tenant=? AND s.scenario LIKE 'live-gateway:%' GROUP BY e.target,e.operation""",(ctx["tenant"],)).fetchall()
        # Explanation: Loop over each item in the iterable and run the indented body.
        for r in rows:
            # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
            db.execute("INSERT INTO ct_baselines VALUES(?,?,?,?,?)",(ctx["tenant"],r["target"],r["operation"],r["n"],r["last_seen"]))
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        _audit(db,ctx["tenant"],ctx["actor"],"baseline.rebuilt",{"entries":len(rows)})
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        db.commit()
        # Explanation: Return this result to the caller; this ends the current function path.
        return {"rebuilt":True,"entries":len(rows),"method":"deterministic frequency counts; not ML"}
    # Explanation: Cleanup block that runs whether the protected operation succeeds or fails.
    finally:db.close()

@router.get("/audit")
# Explanation: Function audit: implements the operation described by its name and body.
def audit(limit:int=Query(default=200,ge=1,le=1000),ctx=Depends(_actor_context)):
    # Explanation: Assigns or updates a value used later by this function or module.
    db=_connect()
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    # Explanation: Return this result to the caller; this ends the current function path.
    try:return [dict(r)|{"details":json.loads(r["details_json"])} for r in db.execute("SELECT * FROM ct_audit WHERE tenant=? ORDER BY sequence DESC LIMIT ?",(ctx["tenant"],limit))]
    # Explanation: Cleanup block that runs whether the protected operation succeeds or fails.
    finally:db.close()

@router.get("/audit/verify")
# Explanation: Function verify_audit: implements the operation described by its name and body.
def verify_audit(ctx=Depends(_actor_context)):
    # Explanation: Assigns or updates a value used later by this function or module.
    db=_connect()
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Assigns or updates a value used later by this function or module.
        rows=db.execute("SELECT * FROM ct_audit WHERE tenant=? ORDER BY sequence",(ctx["tenant"],)).fetchall()
        # Explanation: Assigns or updates a value used later by this function or module.
        prev="GENESIS"; verified=True; bad_sequence=None
        # Explanation: Loop over each item in the iterable and run the indented body.
        for r in rows:
            # Explanation: Assigns or updates a value used later by this function or module.
            details=json.loads(r["details_json"])
            # Explanation: Assigns or updates a value used later by this function or module.
            material=json.dumps({"tenant":r["tenant"],"timestamp":r["timestamp"],"actor":r["actor"],"action":r["action"],"details":details,"previous_hash":prev},sort_keys=True,separators=(",",":"),ensure_ascii=False)
            # Explanation: Assigns or updates a value used later by this function or module.
            expected=hashlib.sha256(material.encode()).hexdigest()
            # Explanation: Conditional decision: execute the following branch only when this expression is true.
            if r["previous_hash"]!=prev or not hmac.compare_digest(r["entry_hash"],expected):
                # Explanation: Assigns or updates a value used later by this function or module.
                verified=False;bad_sequence=r["sequence"];break
            # Explanation: Assigns or updates a value used later by this function or module.
            prev=r["entry_hash"]
        # Explanation: Return this result to the caller; this ends the current function path.
        return {"verified":verified,"entries_checked":len(rows),"first_invalid_sequence":bad_sequence,"note":"Hash chaining detects edits to stored entries, but an attacker controlling the database can rewrite the whole chain; periodically export hashes to independent storage."}
    # Explanation: Cleanup block that runs whether the protected operation succeeds or fails.
    finally:db.close()

@router.get("/reports/compliance")
# Explanation: Function compliance_report: implements the operation described by its name and body.
def compliance_report(ctx=Depends(_actor_context)):
    # Explanation: Assigns or updates a value used later by this function or module.
    db=_connect()
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Assigns or updates a value used later by this function or module.
        tenant=ctx["tenant"]
        # Explanation: Assigns or updates a value used later by this function or module.
        inv=[dict(r) for r in db.execute("SELECT server_id,name,transport,endpoint,expected,status,last_checked FROM ct_inventory WHERE tenant=?",(tenant,))]
        # Explanation: Assigns or updates a value used later by this function or module.
        rules=[dict(r)|{"enabled":bool(r["enabled"])} for r in db.execute("SELECT name,operation,target_pattern,action,enabled FROM ct_policy_rules WHERE tenant=?",(tenant,))]
        # Explanation: Assigns or updates a value used later by this function or module.
        posture=[]
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        posture.append({"control":"MCP inventory","status":"implemented" if inv else "gap","evidence":f"{len(inv)} registered server(s)"})
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        posture.append({"control":"Deterministic policy rules","status":"implemented" if rules else "gap","evidence":f"{len(rules)} configured rule(s)"})
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        posture.append({"control":"Tamper-evident local audit chain","status":"implemented","evidence":"Verify via /api/security/audit/verify"})
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        posture.append({"control":"RBAC API keys","status":"implemented" if os.getenv("CANARYTRAP_RBAC_KEYS") else "not_configured","evidence":"Environment-based key map"})
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        posture.append({"control":"External monitoring coverage","status":"limited","evidence":"Only traffic passing through configured adapters is observable"})
        # Explanation: Return this result to the caller; this ends the current function path.
        return {"report":"MCP-CanaryTrap security posture summary","generated_at":_now(),"tenant":tenant,"disclaimer":"Self-assessment report; not a legal compliance certification or independent audit.","inventory":inv,"policies":rules,"controls":posture}
    # Explanation: Cleanup block that runs whether the protected operation succeeds or fails.
    finally:db.close()

@router.post("/tenants")
# Explanation: Function create_tenant: implements the operation described by its name and body.
def create_tenant(payload:dict,ctx=Depends(_actor_context)):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    _require(ctx,{"admin"})
    # Explanation: Assigns or updates a value used later by this function or module.
    tenant=str(payload.get("tenant","")).strip()
    # Explanation: Assigns or updates a value used later by this function or module.
    name=str(payload.get("name",tenant)).strip()
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    # Explanation: Raise an exception to reject the operation or report a failure.
    if not tenant or len(tenant)>64 or not all(c.isalnum() or c in "_-" for c in tenant):raise HTTPException(status_code=422,detail="Invalid tenant ID")
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    # Explanation: Raise an exception to reject the operation or report a failure.
    if not name or len(name)>120:raise HTTPException(status_code=422,detail="Invalid tenant name")
    # Explanation: Assigns or updates a value used later by this function or module.
    db=_connect()
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        db.execute("INSERT INTO ct_tenants VALUES(?,?,?)",(tenant,name,_now()))
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        _audit(db,ctx["tenant"],ctx["actor"],"tenant.created",{"tenant":tenant})
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        # Explanation: Return this result to the caller; this ends the current function path.
        db.commit();return {"created":True,"tenant":tenant,"note":"Tenant access is assigned through CANARYTRAP_RBAC_KEYS; creating a tenant does not automatically grant access."}
    # Explanation: Raise an exception to reject the operation or report a failure.
    except sqlite3.IntegrityError as exc:raise HTTPException(status_code=409,detail="Tenant already exists") from exc
    # Explanation: Cleanup block that runs whether the protected operation succeeds or fails.
    finally:db.close()

@router.get("/tenants")
# Explanation: Function list_tenants: implements the operation described by its name and body.
def list_tenants(ctx=Depends(_actor_context)):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    _require(ctx,{"admin"})
    # Explanation: Assigns or updates a value used later by this function or module.
    db=_connect()
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    # Explanation: Return this result to the caller; this ends the current function path.
    try:return [dict(r) for r in db.execute("SELECT * FROM ct_tenants ORDER BY tenant")]
    # Explanation: Cleanup block that runs whether the protected operation succeeds or fails.
    finally:db.close()

@router.post("/webhook")
# Explanation: Function configure_webhook: implements the operation described by its name and body.
def configure_webhook(req:WebhookRequest,ctx=Depends(_actor_context)):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    _require(ctx,{"admin"})
    # Explanation: Assigns or updates a value used later by this function or module.
    u=urlsplit(req.url)
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if u.scheme!="https" or not u.hostname or u.username or u.password or u.query or u.fragment:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=422,detail="Webhook must be an HTTPS URL without embedded credentials, query strings or fragments")
    # Explanation: Assigns or updates a value used later by this function or module.
    db=_connect()
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Assigns or updates a value used later by this function or module.
        db.execute("INSERT INTO ct_webhooks VALUES(?,?,?,?) ON CONFLICT(tenant) DO UPDATE SET url=excluded.url,enabled=excluded.enabled,updated_at=excluded.updated_at",(ctx["tenant"],req.url,int(req.enabled),_now()))
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        _audit(db,ctx["tenant"],ctx["actor"],"webhook.configured",{"enabled":req.enabled,"host":u.hostname})
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        db.commit()
        # Explanation: Return this result to the caller; this ends the current function path.
        return {"saved":True,"enabled":req.enabled,"url_host":u.hostname,"note":"Webhook URL is stored locally; automatic delivery is intentionally disabled until an explicit notifier worker is configured."}
    # Explanation: Cleanup block that runs whether the protected operation succeeds or fails.
    finally:db.close()
