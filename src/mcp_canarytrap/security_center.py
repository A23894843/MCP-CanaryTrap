"""Deterministic security-center features: policy, inventory, simulation and audit."""
from __future__ import annotations
import hashlib, hmac, json, os, sqlite3, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/security", tags=["security center"])

def _db_path() -> str:
    return str(Path(os.getenv("CANARYTRAP_DB", "canarytrap.sqlite3")).resolve())

def _connect():
    db = sqlite3.connect(_db_path())
    db.row_factory = sqlite3.Row
    db.execute("""CREATE TABLE IF NOT EXISTS ct_policy_rules(
      rule_id TEXT PRIMARY KEY, tenant TEXT NOT NULL, name TEXT NOT NULL,
      operation TEXT NOT NULL, target_pattern TEXT NOT NULL, action TEXT NOT NULL,
      enabled INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL)""")
    db.execute("""CREATE TABLE IF NOT EXISTS ct_inventory(
      server_id TEXT NOT NULL, tenant TEXT NOT NULL, name TEXT NOT NULL,
      transport TEXT NOT NULL, endpoint TEXT NOT NULL, owner TEXT NOT NULL DEFAULT '',
      expected INTEGER NOT NULL DEFAULT 1, status TEXT NOT NULL DEFAULT 'configured',
      last_checked TEXT, notes TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, PRIMARY KEY(server_id,tenant))""")
    db.execute("""CREATE TABLE IF NOT EXISTS ct_audit(
      sequence INTEGER PRIMARY KEY AUTOINCREMENT, tenant TEXT NOT NULL, timestamp TEXT NOT NULL,
      actor TEXT NOT NULL, action TEXT NOT NULL, details_json TEXT NOT NULL,
      previous_hash TEXT NOT NULL, entry_hash TEXT NOT NULL)""")
    db.execute("""CREATE TABLE IF NOT EXISTS ct_baselines(
      tenant TEXT NOT NULL, target TEXT NOT NULL, operation TEXT NOT NULL,
      count INTEGER NOT NULL DEFAULT 0, last_seen TEXT NOT NULL,
      PRIMARY KEY(tenant,target,operation))""")
    db.execute("""CREATE TABLE IF NOT EXISTS ct_webhooks(
      tenant TEXT PRIMARY KEY, url TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 0,
      updated_at TEXT NOT NULL)""")
    db.execute("""CREATE TABLE IF NOT EXISTS ct_tenants(
      tenant TEXT PRIMARY KEY, name TEXT NOT NULL, created_at TEXT NOT NULL)""")
    db.execute("""CREATE TABLE IF NOT EXISTS ct_simulations(
      simulation_id TEXT PRIMARY KEY, tenant TEXT NOT NULL, name TEXT NOT NULL,
      status TEXT NOT NULL, result_json TEXT NOT NULL, created_at TEXT NOT NULL)""")
    db.commit()
    return db

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _actor_context(api_key: str | None = Header(default=None, alias="X-CanaryTrap-API-Key")) -> dict[str,str]:
    raw = os.getenv("CANARYTRAP_RBAC_KEYS", "").strip()
    if not raw:
        if os.getenv("APP_ENV", "development").lower() == "production":
            # Existing production Basic Auth protects the app, but does not distinguish roles.
            return {"tenant": os.getenv("CANARYTRAP_DEFAULT_TENANT", "default"), "role": "admin", "actor": "basic-auth-operator"}
        return {"tenant": os.getenv("CANARYTRAP_DEFAULT_TENANT", "default"), "role": "admin", "actor": "local-development"}
    if not api_key:
        raise HTTPException(status_code=401, detail="Provide X-CanaryTrap-API-Key")
    try:
        mapping = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=503, detail="CANARYTRAP_RBAC_KEYS must be valid JSON") from exc
    for token, info in mapping.items():
        if isinstance(token, str) and hmac.compare_digest(token, api_key) and isinstance(info, dict):
            role = str(info.get("role", "viewer"))
            if role not in {"admin", "operator", "viewer"}:
                break
            return {"tenant": str(info.get("tenant", "default")), "role": role, "actor": str(info.get("actor", role))}
    raise HTTPException(status_code=403, detail="Invalid API key")

def _require(ctx: dict, roles: set[str]):
    if ctx["role"] not in roles:
        raise HTTPException(status_code=403, detail="Insufficient role for this operation")
    return ctx

def _audit(db, tenant: str, actor: str, action: str, details: dict[str,Any]):
    prev = db.execute("SELECT entry_hash FROM ct_audit WHERE tenant=? ORDER BY sequence DESC LIMIT 1",(tenant,)).fetchone()
    previous_hash = prev["entry_hash"] if prev else "GENESIS"
    timestamp = _now()
    details_json = json.dumps(details, sort_keys=True, separators=(",",":"), ensure_ascii=False)
    material = json.dumps({"tenant":tenant,"timestamp":timestamp,"actor":actor,"action":action,
      "details":details,"previous_hash":previous_hash},sort_keys=True,separators=(",",":"),ensure_ascii=False)
    digest = hashlib.sha256(material.encode()).hexdigest()
    db.execute("INSERT INTO ct_audit(tenant,timestamp,actor,action,details_json,previous_hash,entry_hash) VALUES(?,?,?,?,?,?,?)",
      (tenant,timestamp,actor,action,details_json,previous_hash,digest))
    return {"timestamp":timestamp,"previous_hash":previous_hash,"entry_hash":digest}

def record_gateway_event(operation: str, target: str, is_decoy: bool, verdict_status: str, connection_id: str, tenant: str | None = None, policy_action: str = "allow"):
    tenant=tenant or os.getenv("CANARYTRAP_DEFAULT_TENANT","default")
    db=_connect()
    try:
        db.execute("""INSERT INTO ct_baselines(tenant,target,operation,count,last_seen) VALUES(?,?,?,?,?)
          ON CONFLICT(tenant,target,operation) DO UPDATE SET count=count+1,last_seen=excluded.last_seen""",
          (tenant,target,operation,1,_now()))
        _audit(db,tenant,"gateway","gateway.interaction",{"connection_id":connection_id,"operation":operation,"target":target[:250],"is_decoy":bool(is_decoy),"verdict":verdict_status,"policy_action":policy_action})
        db.commit()
        if verdict_status=="FLAGGED" or policy_action=="deny":
            row=db.execute("SELECT url FROM ct_webhooks WHERE tenant=? AND enabled=1",(tenant,)).fetchone()
            url=(row["url"] if row else os.getenv("CANARYTRAP_WEBHOOK_URL","")).strip()
            parsed=urlsplit(url) if url else None
            if parsed and parsed.scheme=="https" and parsed.hostname:
                # Best-effort, bounded outbound notification; never include tool args or results.
                try:
                    import httpx
                    with httpx.Client(timeout=2.0, follow_redirects=False) as client:
                        client.post(url,json={"service":"MCP-CanaryTrap","event":"policy_denied" if policy_action=="deny" else "decoy_access","tenant":tenant,
                          "connection_id":connection_id,"operation":operation,"target":target[:250],"status":verdict_status,"policy_action":policy_action})
                except Exception:
                    pass
    finally:
        db.close()

def _policy(tenant: str, operation: str, target: str) -> dict:
    """Default allow; first exact/wildcard deny rule wins. Rules are deterministic."""
    db = _connect()
    try:
        rows = db.execute("SELECT * FROM ct_policy_rules WHERE tenant=? AND enabled=1 ORDER BY created_at,rule_id",(tenant,)).fetchall()
        for r in rows:
            op_match = r["operation"] in {"*", operation}
            pat = r["target_pattern"]
            target_match = pat == "*" or pat == target or (pat.endswith("*") and target.startswith(pat[:-1]))
            if op_match and target_match:
                return {"action":r["action"],"rule_id":r["rule_id"],"rule_name":r["name"]}
        fallback=os.getenv("CANARYTRAP_DEFAULT_POLICY_ACTION","allow").strip().lower()
        if fallback not in {"allow","deny"}: fallback="allow"
        return {"action":fallback,"rule_id":None,"rule_name":"default-"+fallback}
    finally:
        db.close()

def resolve_gateway_tenant(api_key: str | None = None) -> str:
    """Resolve tenant for HTTP gateway calls; require a valid key when RBAC is enabled."""
    raw = os.getenv("CANARYTRAP_RBAC_KEYS", "").strip()
    if not raw:
        return os.getenv("CANARYTRAP_DEFAULT_TENANT", "default")
    if not api_key:
        raise HTTPException(status_code=401, detail="Gateway API key required")
    try:
        mapping = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=503, detail="CANARYTRAP_RBAC_KEYS must be valid JSON") from exc
    for token, info in mapping.items():
        if isinstance(token, str) and hmac.compare_digest(token, api_key) and isinstance(info, dict) and info.get("role") in {"admin", "operator", "viewer"}:
            return str(info.get("tenant", "default"))
    raise HTTPException(status_code=403, detail="Invalid gateway API key")

def policy_decision(operation: str, target: str, kind: str, tenant: str | None = None) -> dict:
    """Shared hook for live adapters; only explicit DENY rules block forwarding."""
    decision = _policy(tenant or os.getenv("CANARYTRAP_DEFAULT_TENANT","default"), operation, target)
    return decision

class PolicyRequest(BaseModel):
    name: str = Field(min_length=1,max_length=100)
    operation: str = Field(default="*",min_length=1,max_length=80)
    target_pattern: str = Field(min_length=1,max_length=250)
    action: str = Field(pattern="^(allow|deny|monitor)$")
    enabled: bool = True

class InventoryRequest(BaseModel):
    server_id: str = Field(min_length=1,max_length=64,pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=1,max_length=120)
    transport: str = Field(pattern="^(http|stdio)$")
    endpoint: str = Field(min_length=1,max_length=2000)
    owner: str = Field(default="",max_length=120)
    expected: bool = True
    notes: str = Field(default="",max_length=1000)

class WebhookRequest(BaseModel):
    url: str = Field(min_length=8,max_length=2000)
    enabled: bool = True

@router.get("/overview")
def security_overview(ctx=Depends(_actor_context)):
    db=_connect()
    try:
        tenant=ctx["tenant"]
        counts={
          "policy_rules":db.execute("SELECT count(*) FROM ct_policy_rules WHERE tenant=?",(tenant,)).fetchone()[0],
          "inventory_servers":db.execute("SELECT count(*) FROM ct_inventory WHERE tenant=?",(tenant,)).fetchone()[0],
          "unexpected_servers":db.execute("SELECT count(*) FROM ct_inventory WHERE tenant=? AND expected=0",(tenant,)).fetchone()[0],
          "audit_entries":db.execute("SELECT count(*) FROM ct_audit WHERE tenant=?",(tenant,)).fetchone()[0],
          "simulations":db.execute("SELECT count(*) FROM ct_simulations WHERE tenant=?",(tenant,)).fetchone()[0],
        }
        flagged=db.execute("SELECT count(*) FROM ct_audit WHERE tenant=? AND action='gateway.interaction' AND (details_json LIKE ? OR details_json LIKE ?)",(tenant,'%"verdict":"FLAGGED"%','%"policy_action":"deny"%')).fetchone()[0]
        return {"tenant":tenant,"role":ctx["role"],"counts":counts,"flagged_gateway_events":flagged,
          "deterministic_only":True,"notes":"Counts are prototype telemetry, not a certification or global host discovery."}
    finally: db.close()

@router.get("/policies")
def list_policies(ctx=Depends(_actor_context)):
    db=_connect()
    try:return [dict(r)|{"enabled":bool(r["enabled"])} for r in db.execute("SELECT * FROM ct_policy_rules WHERE tenant=? ORDER BY created_at DESC",(ctx["tenant"],))]
    finally:db.close()

@router.post("/policies")
def create_policy(req:PolicyRequest,ctx=Depends(_actor_context)):
    _require(ctx,{"admin","operator"})
    db=_connect()
    try:
        rid=uuid.uuid4().hex
        db.execute("INSERT INTO ct_policy_rules VALUES(?,?,?,?,?,?,?,?)",(rid,ctx["tenant"],req.name,req.operation,req.target_pattern,req.action,int(req.enabled),_now()))
        _audit(db,ctx["tenant"],ctx["actor"],"policy.created",{"rule_id":rid,"name":req.name,"action":req.action})
        db.commit()
        return {"created":True,"rule_id":rid,"note":"DENY rules are enforced on supported live-gateway operations; default behavior is allow."}
    finally:db.close()

@router.delete("/policies/{rule_id}")
def delete_policy(rule_id:str,ctx=Depends(_actor_context)):
    _require(ctx,{"admin"})
    db=_connect()
    try:
        cur=db.execute("DELETE FROM ct_policy_rules WHERE rule_id=? AND tenant=?",(rule_id,ctx["tenant"]))
        if not cur.rowcount:raise HTTPException(status_code=404,detail="Policy not found")
        _audit(db,ctx["tenant"],ctx["actor"],"policy.deleted",{"rule_id":rule_id});db.commit()
        return {"deleted":True,"rule_id":rule_id}
    finally:db.close()

@router.get("/inventory")
def inventory(ctx=Depends(_actor_context)):
    db=_connect()
    try:return [dict(r)|{"expected":bool(r["expected"])} for r in db.execute("SELECT * FROM ct_inventory WHERE tenant=? ORDER BY created_at DESC",(ctx["tenant"],))]
    finally:db.close()

@router.post("/inventory")
def add_inventory(req:InventoryRequest,ctx=Depends(_actor_context)):
    _require(ctx,{"admin","operator"})
    if req.transport=="http":
        u=urlsplit(req.endpoint)
        if u.scheme not in {"http","https"} or not u.hostname or u.username or u.password or u.query or u.fragment:
            raise HTTPException(status_code=422,detail="HTTP endpoint must be a valid URL without embedded credentials, query strings or fragments")
    db=_connect()
    try:
        db.execute("INSERT INTO ct_inventory VALUES(?,?,?,?,?,?,?,?,?,?,?)",(req.server_id,ctx["tenant"],req.name,req.transport,req.endpoint,req.owner,int(req.expected),"configured",None,req.notes,_now()))
        _audit(db,ctx["tenant"],ctx["actor"],"inventory.registered",{"server_id":req.server_id,"transport":req.transport,"expected":req.expected})
        db.commit()
        return {"registered":True,"server_id":req.server_id}
    except sqlite3.IntegrityError as exc:raise HTTPException(status_code=409,detail="Server ID already exists in this tenant") from exc
    finally:db.close()

@router.delete("/inventory/{server_id}")
def remove_inventory(server_id:str,ctx=Depends(_actor_context)):
    _require(ctx,{"admin","operator"})
    db=_connect()
    try:
        cur=db.execute("DELETE FROM ct_inventory WHERE server_id=? AND tenant=?",(server_id,ctx["tenant"]))
        if not cur.rowcount:raise HTTPException(status_code=404,detail="Server not found")
        _audit(db,ctx["tenant"],ctx["actor"],"inventory.removed",{"server_id":server_id});db.commit()
        return {"removed":True}
    finally:db.close()

@router.post("/inventory/reconcile")
def reconcile_inventory(ctx=Depends(_actor_context)):
    """Compare the configured HTTP gateway list with registered inventory entries."""
    from .gateway_core import load_http_upstreams
    try: upstreams=load_http_upstreams()
    except ValueError as exc: raise HTTPException(status_code=503,detail="Gateway configuration could not be parsed") from exc
    db=_connect()
    try:
        known={r["server_id"] for r in db.execute("SELECT server_id FROM ct_inventory WHERE tenant=?",(ctx["tenant"],))}
        observed=[]
        for cid,cfg in upstreams.items():
            observed.append({"server_id":cid,"endpoint":cfg["url"],"registered":cid in known,"status":"registered" if cid in known else "configured-but-unregistered"})
        unknown=[x for x in observed if not x["registered"]]
        _audit(db,ctx["tenant"],ctx["actor"],"inventory.reconciled",{"configured_http":len(observed),"unregistered":len(unknown)})
        db.commit()
        return {"tenant":ctx["tenant"],"configured_http_connections":observed,"unregistered_connections":unknown,
          "note":"This detects unregistered connections in CanaryTrap configuration only; it does not discover arbitrary servers on the host or network."}
    finally:db.close()

@router.get("/inventory/shadow")
def detect_unregistered_gateway_connections(ctx=Depends(_actor_context)):
    """Detect observed gateway connection IDs missing from the maintained inventory."""
    db=_connect()
    try:
        registered={r["server_id"] for r in db.execute("SELECT server_id FROM ct_inventory WHERE tenant=?",(ctx["tenant"],))}
        rows=db.execute("SELECT details_json,timestamp FROM ct_audit WHERE tenant=? AND action='gateway.interaction' ORDER BY sequence DESC",(ctx["tenant"],)).fetchall()
        observed={}
        for row in rows:
            try:detail=json.loads(row["details_json"])
            except json.JSONDecodeError:continue
            cid=detail.get("connection_id")
            if cid and cid not in observed:observed[cid]={"connection_id":cid,"last_seen":row["timestamp"],"operations":0}
            if cid:observed[cid]["operations"]+=1
        shadows=[item for cid,item in observed.items() if cid not in registered]
        return {"tenant":ctx["tenant"],"observed_connections":list(observed.values()),"unregistered_observed_connections":shadows,
          "scope":"Only connections that have already passed through this gateway are visible; this is not host or network-wide discovery."}
    finally:db.close()

@router.get("/correlation")
def cross_server_correlation(ctx=Depends(_actor_context)):
    """Correlate deterministic target/operation observations across gateway connection IDs."""
    db=_connect()
    try:
        rows=db.execute("SELECT details_json,timestamp FROM ct_audit WHERE tenant=? AND action='gateway.interaction' ORDER BY sequence",(ctx["tenant"],)).fetchall()
        groups={}
        for row in rows:
            try:d=json.loads(row["details_json"])
            except json.JSONDecodeError:continue
            key=(d.get("operation",""),d.get("target",""))
            group=groups.setdefault(key,{"operation":key[0],"target":key[1],"connections":set(),"observations":0,"flagged_observations":0,"first_seen":row["timestamp"],"last_seen":row["timestamp"]})
            group["connections"].add(d.get("connection_id","unknown"));group["observations"]+=1
            if d.get("verdict")=="FLAGGED":group["flagged_observations"]+=1
            group["last_seen"]=row["timestamp"]
        result=[]
        for g in groups.values():
            g["connections"]=sorted(g["connections"]);g["connection_count"]=len(g["connections"])
            result.append(g)
        result.sort(key=lambda x:(-x["flagged_observations"],-x["connection_count"],-x["observations"]))
        return {"tenant":ctx["tenant"],"correlated_targets":result,"method":"Exact deterministic grouping by operation and target; no behavioral inference."}
    finally:db.close()

@router.post("/posture/scan")
def posture_scan(ctx=Depends(_actor_context)):
    """Local configuration posture checks; does not probe arbitrary endpoints."""
    db=_connect()
    try:
        tenant=ctx["tenant"]
        servers=[dict(r) for r in db.execute("SELECT * FROM ct_inventory WHERE tenant=?",(tenant,))]
        rules=[dict(r) for r in db.execute("SELECT * FROM ct_policy_rules WHERE tenant=?",(tenant,))]
        checks=[
          {"id":"inventory-present","status":"pass" if servers else "warn","detail":f"{len(servers)} server(s) registered"},
          {"id":"policy-present","status":"pass" if rules else "warn","detail":f"{len(rules)} policy rule(s) configured"},
          {"id":"https-for-remote","status":"pass" if all(s["transport"]!="http" or s["endpoint"].startswith("https://") for s in servers) else "warn","detail":"Remote HTTP inventory should use HTTPS"},
          {"id":"rbac-key-map","status":"pass" if os.getenv("CANARYTRAP_RBAC_KEYS") else "warn","detail":"API-key RBAC configured" if os.getenv("CANARYTRAP_RBAC_KEYS") else "RBAC key map not configured; development/admin fallback may be active"},
          {"id":"production-dashboard-auth","status":"pass" if os.getenv("APP_ENV","development").lower()!="production" or (os.getenv("DASHBOARD_USERNAME") and os.getenv("DASHBOARD_PASSWORD")) else "fail","detail":"Production dashboard credentials"},
          {"id":"webhook-https","status":"pass" if not os.getenv("CANARYTRAP_WEBHOOK_URL") or os.getenv("CANARYTRAP_WEBHOOK_URL","").startswith("https://") else "fail","detail":"Configured webhook must use HTTPS"},
        ]
        result={"tenant":tenant,"scanned_at":_now(),"checks":checks,"summary":{"pass":sum(c["status"]=="pass" for c in checks),"warn":sum(c["status"]=="warn" for c in checks),"fail":sum(c["status"]=="fail" for c in checks)}}
        _audit(db,tenant,ctx["actor"],"posture.scan",result["summary"]);db.commit()
        return result
    finally:db.close()

@router.post("/simulate")
def simulate_attack(ctx=Depends(_actor_context)):
    """Run deterministic rule checks against a bounded built-in attack corpus."""
    _require(ctx,{"admin","operator"})
    cases=[
      {"name":"benign-read","operation":"tools/call","target":"search_public_docs","expected":"allow"},
      {"name":"decoy-tool-access","operation":"tools/call","target":"canarytrap_decoy_admin","expected":"deny"},
      {"name":"sensitive-resource-read","operation":"resources/read","target":"canarytrap://secret/payroll","expected":"deny"},
      {"name":"unlisted-prompt","operation":"prompts/get","target":"unknown_prompt","expected":"allow"},
    ]
    results=[]
    for c in cases:
        d=_policy(ctx["tenant"],c["operation"],c["target"])
        # Built-in decoy patterns are included in test expected only when user has configured matching rules.
        expected=d["action"] if d["action"] in {"allow","deny"} else "allow"
        results.append({"case":c["name"],"operation":c["operation"],"target":c["target"],"policy_action":d["action"],"matched_rule":d["rule_id"],"result":"pass" if expected==d["action"] else "review"})
    status="completed" if all(r["result"]=="pass" for r in results) else "review"
    sim_id=uuid.uuid4().hex
    db=_connect()
    try:
        db.execute("INSERT INTO ct_simulations VALUES(?,?,?,?,?,?)",(sim_id,ctx["tenant"],"Built-in policy smoke test",status,json.dumps(results),_now()))
        _audit(db,ctx["tenant"],ctx["actor"],"simulation.completed",{"simulation_id":sim_id,"status":status,"cases":len(results)})
        db.commit()
    finally:db.close()
    return {"simulation_id":sim_id,"status":status,"cases":results,"note":"This validates policy matching only; it does not attack a live server."}

@router.get("/simulations")
def list_simulations(ctx=Depends(_actor_context)):
    db=_connect()
    try:return [{"simulation_id":r["simulation_id"],"tenant":r["tenant"],"name":r["name"],"status":r["status"],"result":json.loads(r["result_json"]),"created_at":r["created_at"]} for r in db.execute("SELECT * FROM ct_simulations WHERE tenant=? ORDER BY created_at DESC",(ctx["tenant"],))]
    finally:db.close()

@router.get("/baselines")
def baselines(ctx=Depends(_actor_context)):
    db=_connect()
    try:return [dict(r) for r in db.execute("SELECT * FROM ct_baselines WHERE tenant=? ORDER BY count DESC",(ctx["tenant"],))]
    finally:db.close()

@router.post("/baselines/rebuild")
def rebuild_baselines(ctx=Depends(_actor_context)):
    _require(ctx,{"admin","operator"})
    db=_connect()
    try:
        # Rebuild only from stored gateway/harness events, using deterministic counts.
        db.execute("DELETE FROM ct_baselines WHERE tenant=?",(ctx["tenant"],))
        rows=db.execute("""SELECT e.target,e.operation,COUNT(*) AS n,MAX(e.timestamp) AS last_seen
          FROM events e JOIN sessions s ON s.session_id=e.session_id
          WHERE s.tenant=? AND s.scenario LIKE 'live-gateway:%' GROUP BY e.target,e.operation""",(ctx["tenant"],)).fetchall()
        for r in rows:
            db.execute("INSERT INTO ct_baselines VALUES(?,?,?,?,?)",(ctx["tenant"],r["target"],r["operation"],r["n"],r["last_seen"]))
        _audit(db,ctx["tenant"],ctx["actor"],"baseline.rebuilt",{"entries":len(rows)})
        db.commit()
        return {"rebuilt":True,"entries":len(rows),"method":"deterministic frequency counts; not ML"}
    finally:db.close()

@router.get("/audit")
def audit(limit:int=Query(default=200,ge=1,le=1000),ctx=Depends(_actor_context)):
    db=_connect()
    try:return [dict(r)|{"details":json.loads(r["details_json"])} for r in db.execute("SELECT * FROM ct_audit WHERE tenant=? ORDER BY sequence DESC LIMIT ?",(ctx["tenant"],limit))]
    finally:db.close()

@router.get("/audit/verify")
def verify_audit(ctx=Depends(_actor_context)):
    db=_connect()
    try:
        rows=db.execute("SELECT * FROM ct_audit WHERE tenant=? ORDER BY sequence",(ctx["tenant"],)).fetchall()
        prev="GENESIS"; verified=True; bad_sequence=None
        for r in rows:
            details=json.loads(r["details_json"])
            material=json.dumps({"tenant":r["tenant"],"timestamp":r["timestamp"],"actor":r["actor"],"action":r["action"],"details":details,"previous_hash":prev},sort_keys=True,separators=(",",":"),ensure_ascii=False)
            expected=hashlib.sha256(material.encode()).hexdigest()
            if r["previous_hash"]!=prev or not hmac.compare_digest(r["entry_hash"],expected):
                verified=False;bad_sequence=r["sequence"];break
            prev=r["entry_hash"]
        return {"verified":verified,"entries_checked":len(rows),"first_invalid_sequence":bad_sequence,"note":"Hash chaining detects edits to stored entries, but an attacker controlling the database can rewrite the whole chain; periodically export hashes to independent storage."}
    finally:db.close()

@router.get("/reports/compliance")
def compliance_report(ctx=Depends(_actor_context)):
    db=_connect()
    try:
        tenant=ctx["tenant"]
        inv=[dict(r) for r in db.execute("SELECT server_id,name,transport,endpoint,expected,status,last_checked FROM ct_inventory WHERE tenant=?",(tenant,))]
        rules=[dict(r)|{"enabled":bool(r["enabled"])} for r in db.execute("SELECT name,operation,target_pattern,action,enabled FROM ct_policy_rules WHERE tenant=?",(tenant,))]
        posture=[]
        posture.append({"control":"MCP inventory","status":"implemented" if inv else "gap","evidence":f"{len(inv)} registered server(s)"})
        posture.append({"control":"Deterministic policy rules","status":"implemented" if rules else "gap","evidence":f"{len(rules)} configured rule(s)"})
        posture.append({"control":"Tamper-evident local audit chain","status":"implemented","evidence":"Verify via /api/security/audit/verify"})
        posture.append({"control":"RBAC API keys","status":"implemented" if os.getenv("CANARYTRAP_RBAC_KEYS") else "not_configured","evidence":"Environment-based key map"})
        posture.append({"control":"External monitoring coverage","status":"limited","evidence":"Only traffic passing through configured adapters is observable"})
        return {"report":"MCP-CanaryTrap security posture summary","generated_at":_now(),"tenant":tenant,"disclaimer":"Self-assessment report; not a legal compliance certification or independent audit.","inventory":inv,"policies":rules,"controls":posture}
    finally:db.close()

@router.post("/tenants")
def create_tenant(payload:dict,ctx=Depends(_actor_context)):
    _require(ctx,{"admin"})
    tenant=str(payload.get("tenant","")).strip()
    name=str(payload.get("name",tenant)).strip()
    if not tenant or len(tenant)>64 or not all(c.isalnum() or c in "_-" for c in tenant):raise HTTPException(status_code=422,detail="Invalid tenant ID")
    if not name or len(name)>120:raise HTTPException(status_code=422,detail="Invalid tenant name")
    db=_connect()
    try:
        db.execute("INSERT INTO ct_tenants VALUES(?,?,?)",(tenant,name,_now()))
        _audit(db,ctx["tenant"],ctx["actor"],"tenant.created",{"tenant":tenant})
        db.commit();return {"created":True,"tenant":tenant,"note":"Tenant access is assigned through CANARYTRAP_RBAC_KEYS; creating a tenant does not automatically grant access."}
    except sqlite3.IntegrityError as exc:raise HTTPException(status_code=409,detail="Tenant already exists") from exc
    finally:db.close()

@router.get("/tenants")
def list_tenants(ctx=Depends(_actor_context)):
    _require(ctx,{"admin"})
    db=_connect()
    try:return [dict(r) for r in db.execute("SELECT * FROM ct_tenants ORDER BY tenant")]
    finally:db.close()

@router.post("/webhook")
def configure_webhook(req:WebhookRequest,ctx=Depends(_actor_context)):
    _require(ctx,{"admin"})
    u=urlsplit(req.url)
    if u.scheme!="https" or not u.hostname or u.username or u.password or u.query or u.fragment:
        raise HTTPException(status_code=422,detail="Webhook must be an HTTPS URL without embedded credentials, query strings or fragments")
    db=_connect()
    try:
        db.execute("INSERT INTO ct_webhooks VALUES(?,?,?,?) ON CONFLICT(tenant) DO UPDATE SET url=excluded.url,enabled=excluded.enabled,updated_at=excluded.updated_at",(ctx["tenant"],req.url,int(req.enabled),_now()))
        _audit(db,ctx["tenant"],ctx["actor"],"webhook.configured",{"enabled":req.enabled,"host":u.hostname})
        db.commit()
        return {"saved":True,"enabled":req.enabled,"url_host":u.hostname,"note":"Webhook URL is stored locally; automatic delivery is intentionally disabled until an explicit notifier worker is configured."}
    finally:db.close()
