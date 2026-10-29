# Annotated source file for MCP-CanaryTrap v1.3.2.
# Lines beginning with "Explanation:" describe the following statement or branch.
# Original executable statements are preserved; comments are for learning.

# Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
"""FastAPI reporting API and minimal browser dashboard."""
# Explanation: Imports names from pathlib.
from pathlib import Path
# Explanation: Imports names from fastapi.
from fastapi import FastAPI, HTTPException, Query, Request, Depends
# Explanation: Imports names from pydantic.
from pydantic import BaseModel, Field
# Explanation: Imports names from fastapi.responses.
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
# Explanation: Imports modules that this file uses.
import uvicorn
# Explanation: Imports modules that this file uses.
import hmac
# Explanation: Imports modules that this file uses.
import os
# Explanation: Imports modules that this file uses.
import re
# Explanation: Imports modules that this file uses.
import json
# Explanation: Imports modules that this file uses.
import httpx
# Explanation: Imports modules that this file uses.
import hashlib
# Explanation: Imports modules that this file uses.
import secrets
# Explanation: Imports modules that this file uses.
import sqlite3
# Explanation: Imports modules that this file uses.
import time
# Explanation: Imports names from urllib.parse.
from urllib.parse import urlsplit
# Explanation: Imports names from harness.
from .harness import DemoHarness
# Explanation: Imports names from storage.
from .storage import Store
# Explanation: Imports names from http_gateway.
from .http_gateway import router as http_gateway_router
# Explanation: Imports names from gateway_core.
from .gateway_core import load_http_upstreams
# Explanation: Imports names from security_center.
from .security_center import router as security_center_router, _actor_context, _require
# Explanation: Imports names from gateway_core.
from .gateway_core import validate_upstream_url

# Explanation: Sets a module-level constant or configuration value.
APP_ENV = os.getenv("APP_ENV", "production").strip().lower()
# Explanation: Sets a module-level constant or configuration value.
DASHBOARD_USERNAME = os.getenv("DASHBOARD_USERNAME", "")
# Explanation: Sets a module-level constant or configuration value.
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "")

# Explanation: Assigns or updates a value used later by this function or module.
app = FastAPI(title="MCP-CanaryTrap", version="1.3.1",
              description="MCP decoy monitoring prototype with stdio and Streamable HTTP gateway adapters.")
# Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
app.include_router(http_gateway_router)
# Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
app.include_router(security_center_router)


# Explanation: Sets a module-level constant or configuration value.
AUTH_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MCP-CanaryTrap · Secure sign in</title>
<style>
:root{color-scheme:light;font-family:Inter,system-ui,-apple-system,sans-serif;background:#f4f7fb;color:#182538}*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;padding:24px;background:radial-gradient(ellipse at top,#e6efff 0,#f4f7fb 58%)}main{width:min(440px,100%);padding:30px;border:1px solid #dce4ef;border-radius:18px;background:#fff;box-shadow:0 24px 70px #20324a18}h1{font-size:1.45rem;margin:0 0 8px}p{color:#5e6e83;line-height:1.6}label{display:block;font-size:.9rem;margin:16px 0 7px}input{width:100%;padding:12px;border:1px solid #cbd6e5;border-radius:9px;background:#fff;color:#182538;font:inherit}button{width:100%;margin-top:20px;padding:12px;border:0;border-radius:9px;background:#245fcb;color:#fff;font-weight:750;font:inherit;cursor:pointer}.notice{padding:10px;border-radius:8px;background:#eef4ff;color:#244c8d;font-size:.9rem}.error{color:#b42332}.hint{font-size:.82rem}.hidden{display:none}</style></head>
<body><main><p class="notice" id="modeBadge">MCP-CanaryTrap · Protected dashboard</p><p class="hint">A simple, secure sign-in to your security test dashboard.</p><h1 id="heading">Administrator setup</h1><p id="intro">Create the first administrator account for this dashboard. This setup is available only once.</p>
<form id="authForm"><label for="username">Username</label><input id="username" name="username" autocomplete="username" minlength="3" maxlength="64" required><div id="confirmWrap"><label for="password">Password</label><input id="password" name="password" type="password" autocomplete="new-password" minlength="16" maxlength="256" required><label for="confirmPassword">Confirm password</label><input id="confirmPassword" name="confirmPassword" type="password" autocomplete="new-password" minlength="16" maxlength="256" required><p class="hint">Use a unique password of at least 16 characters. Keep it private and do not reuse a password from another account.</p></div><p id="message" role="status" class="error"></p><button id="submitButton" type="submit">Create administrator</button></form></main>
<script>
const setupMode=__SETUP_MODE__;const form=document.getElementById('authForm');const heading=document.getElementById('heading');const intro=document.getElementById('intro');const badge=document.getElementById('modeBadge');const confirmWrap=document.getElementById('confirmWrap');const button=document.getElementById('submitButton');const message=document.getElementById('message');
if(setupMode){document.getElementById('username').autocomplete='username';}else{heading.textContent='Sign in';intro.textContent='Sign in to open your dashboard. Your account protects the saved tests, activity, and settings.';badge.textContent='MCP-CanaryTrap · Sign in';confirmWrap.classList.add('hidden');document.getElementById('password').autocomplete='current-password';document.getElementById('password').minLength=1;document.getElementById('confirmPassword').required=false;button.textContent='Sign in';}
form.addEventListener('submit',async e=>{e.preventDefault();message.textContent='';const username=document.getElementById('username').value.trim();const password=document.getElementById('password').value;const payload={username,password};if(setupMode&&password!==document.getElementById('confirmPassword').value){message.textContent='Passwords do not match.';return;}button.disabled=true;button.textContent='Please wait…';try{const response=await fetch(setupMode?'/api/auth/setup':'/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});let result={};try{result=await response.json()}catch{}if(!response.ok)throw new Error(result.detail||'Authentication failed. Please try again.');window.location.assign('/');}catch(err){message.textContent=err.message||'Could not contact the server.';}finally{button.disabled=false;button.textContent=setupMode?'Create administrator':'Sign in';}});
</script></body></html>"""

# Explanation: Sets a module-level constant or configuration value.
_PUBLIC_AUTH_PATHS = {"/health", "/ready", "/login", "/setup", "/api/auth/setup", "/api/auth/login", "/api/auth/logout"}
# Explanation: Sets a module-level constant or configuration value.
_SESSION_COOKIE = "canarytrap_session"
# Explanation: Sets a module-level constant or configuration value.
_SESSION_TTL = 12 * 60 * 60


# Explanation: Function _auth_db_path: implements the operation described by its name and body.
def _auth_db_path() -> str:
    # Explanation: Assigns or updates a value used later by this function or module.
    path = Path(os.getenv("CANARYTRAP_DB", "canarytrap.sqlite3")).expanduser()
    # Explanation: Assigns or updates a value used later by this function or module.
    path.parent.mkdir(parents=True, exist_ok=True)
    # Explanation: Return this result to the caller; this ends the current function path.
    return str(path)


# Explanation: Function _auth_connect: implements the operation described by its name and body.
def _auth_connect():
    # Explanation: Assigns or updates a value used later by this function or module.
    db = sqlite3.connect(_auth_db_path(), timeout=10)
    # Explanation: Assigns or updates a value used later by this function or module.
    db.execute("CREATE TABLE IF NOT EXISTS ct_dashboard_auth (id INTEGER PRIMARY KEY CHECK(id=1), username TEXT NOT NULL, salt TEXT NOT NULL, password_hash TEXT NOT NULL, created_at INTEGER NOT NULL)")
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    db.execute("CREATE TABLE IF NOT EXISTS ct_dashboard_sessions (token_hash TEXT PRIMARY KEY, expires_at INTEGER NOT NULL)")
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    db.commit()
    # Explanation: Return this result to the caller; this ends the current function path.
    return db


# Explanation: Function _stored_account: implements the operation described by its name and body.
def _stored_account():
    # Explanation: Acquire/manage the context resource and release it reliably on exit.
    with _auth_connect() as db:
        # Explanation: Assigns or updates a value used later by this function or module.
        row = db.execute("SELECT username, salt, password_hash FROM ct_dashboard_auth WHERE id=1").fetchone()
    # Explanation: Return this result to the caller; this ends the current function path.
    return row


# Explanation: Function _auth_config_state: implements the operation described by its name and body.
def _auth_config_state() -> str:
    # Environment variables are the preferred deployment mechanism. A database
    # account is the first-run fallback for deployments configured through UI.
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if bool(DASHBOARD_USERNAME) != bool(DASHBOARD_PASSWORD):
        # Explanation: Return this result to the caller; this ends the current function path.
        return "partial-env"
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if DASHBOARD_USERNAME and DASHBOARD_PASSWORD:
        # Explanation: Return this result to the caller; this ends the current function path.
        return "configured"
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Return this result to the caller; this ends the current function path.
        return "configured" if _stored_account() else "setup"
    except (sqlite3.Error, OSError):
        # Explanation: Return this result to the caller; this ends the current function path.
        return "database-error"


# Explanation: Function _password_hash: implements the operation described by its name and body.
def _password_hash(password: str, salt: bytes) -> str:
    # Explanation: Return this result to the caller; this ends the current function path.
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32).hex()


# Explanation: Function _credentials_valid: implements the operation described by its name and body.
def _credentials_valid(username: str, password: str) -> bool:
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if DASHBOARD_USERNAME and DASHBOARD_PASSWORD:
        # Explanation: Return this result to the caller; this ends the current function path.
        return hmac.compare_digest(username, DASHBOARD_USERNAME) and hmac.compare_digest(password, DASHBOARD_PASSWORD)
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Assigns or updates a value used later by this function or module.
        account = _stored_account()
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        if not account:
            # Explanation: Return this result to the caller; this ends the current function path.
            return False
        # Explanation: Assigns or updates a value used later by this function or module.
        saved_username, salt_hex, saved_hash = account
        # Explanation: Assigns or updates a value used later by this function or module.
        actual_hash = _password_hash(password, bytes.fromhex(salt_hex))
        # Explanation: Return this result to the caller; this ends the current function path.
        return hmac.compare_digest(username, saved_username) and hmac.compare_digest(actual_hash, saved_hash)
    except (sqlite3.Error, OSError, ValueError):
        # Explanation: Return this result to the caller; this ends the current function path.
        return False


# Explanation: Function _session_valid: implements the operation described by its name and body.
def _session_valid(request: Request) -> bool:
    # Explanation: Assigns or updates a value used later by this function or module.
    token = request.cookies.get(_SESSION_COOKIE, "")
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if not token or len(token) > 200:
        # Explanation: Return this result to the caller; this ends the current function path.
        return False
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Acquire/manage the context resource and release it reliably on exit.
        with _auth_connect() as db:
            # Explanation: Assigns or updates a value used later by this function or module.
            row = db.execute("SELECT expires_at FROM ct_dashboard_sessions WHERE token_hash=?", (hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
            # Explanation: Conditional decision: execute the following branch only when this expression is true.
            if not row:
                # Explanation: Return this result to the caller; this ends the current function path.
                return False
            # Explanation: Conditional decision: execute the following branch only when this expression is true.
            if int(row[0]) <= int(time.time()):
                # Explanation: Assigns or updates a value used later by this function or module.
                db.execute("DELETE FROM ct_dashboard_sessions WHERE token_hash=?", (hashlib.sha256(token.encode()).hexdigest(),))
                # Explanation: Return this result to the caller; this ends the current function path.
                return False
            # Explanation: Return this result to the caller; this ends the current function path.
            return True
    except (sqlite3.Error, OSError):
        # Explanation: Return this result to the caller; this ends the current function path.
        return False


# Explanation: Function _issue_session: implements the operation described by its name and body.
def _issue_session(response, request: Request) -> None:
    # Explanation: Assigns or updates a value used later by this function or module.
    token = secrets.token_urlsafe(32)
    # Explanation: Assigns or updates a value used later by this function or module.
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    # Explanation: Assigns or updates a value used later by this function or module.
    expires = int(time.time()) + _SESSION_TTL
    # Explanation: Acquire/manage the context resource and release it reliably on exit.
    with _auth_connect() as db:
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        db.execute("INSERT INTO ct_dashboard_sessions(token_hash, expires_at) VALUES(?,?)", (token_hash, expires))
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        db.execute("DELETE FROM ct_dashboard_sessions WHERE expires_at<=?", (int(time.time()),))
    # Explanation: Assigns or updates a value used later by this function or module.
    response.set_cookie(_SESSION_COOKIE, token, max_age=_SESSION_TTL, httponly=True,
                        secure=request.url.scheme == "https", samesite="strict", path="/")


# Explanation: Function _auth_page: implements the operation described by its name and body.
def _auth_page(setup_mode: bool) -> HTMLResponse:
    # Explanation: Return this result to the caller; this ends the current function path.
    return HTMLResponse(AUTH_PAGE.replace("__SETUP_MODE__", "true" if setup_mode else "false"))


@app.middleware("http")
# Explanation: Async function security_and_production_auth: performs asynchronous work; inspect awaited calls and returned result.
async def security_and_production_auth(request: Request, call_next):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Protect production routes; provide safe first-run setup and browser login pages."""
    # Explanation: Assigns or updates a value used later by this function or module.
    path = request.url.path
    # Explanation: Assigns or updates a value used later by this function or module.
    response = None
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if APP_ENV == "production" and path not in _PUBLIC_AUTH_PATHS:
        # Explanation: Assigns or updates a value used later by this function or module.
        state = _auth_config_state()
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        if state == "database-error":
            # Explanation: Assigns or updates a value used later by this function or module.
            response = JSONResponse(status_code=503, content={"detail": "Authentication storage is unavailable. Check CANARYTRAP_DB permissions and restart the service."})
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        elif state == "partial-env":
            # Explanation: Assigns or updates a value used later by this function or module.
            response = JSONResponse(status_code=503, content={"detail": "Set both DASHBOARD_USERNAME and DASHBOARD_PASSWORD, or remove both to use first-run setup."})
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        elif state == "setup":
            # Explanation: Conditional decision: execute the following branch only when this expression is true.
            if path.startswith("/api/") or path.endswith(".json"):
                # Explanation: Assigns or updates a value used later by this function or module.
                response = JSONResponse(status_code=503, content={"detail": "Administrator setup is required. Open /setup in your browser first."})
            else:
                # Explanation: Assigns or updates a value used later by this function or module.
                response = _auth_page(True)
        else:
            # Explanation: Assigns or updates a value used later by this function or module.
            authenticated = _session_valid(request)
            # Explanation: Assigns or updates a value used later by this function or module.
            auth = request.headers.get("authorization", "")
            # Explanation: Conditional decision: execute the following branch only when this expression is true.
            if not authenticated and auth.startswith("Basic "):
                # Explanation: Imports modules that this file uses.
                import base64
                # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
                try:
                    # Explanation: Assigns or updates a value used later by this function or module.
                    decoded = base64.b64decode(auth[6:], validate=True).decode("utf-8")
                    # Explanation: Assigns or updates a value used later by this function or module.
                    username, password = decoded.split(":", 1)
                    # Explanation: Assigns or updates a value used later by this function or module.
                    authenticated = _credentials_valid(username, password)
                except (ValueError, UnicodeDecodeError):
                    # Explanation: Assigns or updates a value used later by this function or module.
                    authenticated = False
            # Explanation: Conditional decision: execute the following branch only when this expression is true.
            if not authenticated:
                # Explanation: Conditional decision: execute the following branch only when this expression is true.
                if path.startswith("/api/") or path.endswith(".json"):
                    # Explanation: Assigns or updates a value used later by this function or module.
                    response = JSONResponse(status_code=401, content={"detail": "Authentication required. Sign in at /login."})
                else:
                    # Explanation: Assigns or updates a value used later by this function or module.
                    response = _auth_page(False)
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if response is None:
        # Explanation: Assigns or updates a value used later by this function or module.
        response = await call_next(request)
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    response.headers.setdefault("X-Frame-Options", "DENY")
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    response.headers.setdefault("Cache-Control", "no-store")
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if APP_ENV == "production":
        # Explanation: Assigns or updates a value used later by this function or module.
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    # Explanation: Return this result to the caller; this ends the current function path.
    return response


@app.get("/setup", response_class=HTMLResponse, include_in_schema=False)
# Explanation: Function first_run_setup_page: implements the operation described by its name and body.
def first_run_setup_page():
    # Explanation: Assigns or updates a value used later by this function or module.
    state = _auth_config_state()
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if APP_ENV != "production" or state != "setup":
        # Explanation: Return this result to the caller; this ends the current function path.
        return RedirectResponse(url="/login", status_code=303)
    # Explanation: Return this result to the caller; this ends the current function path.
    return _auth_page(True)


@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
# Explanation: Function login_page: implements the operation described by its name and body.
def login_page():
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if APP_ENV == "production" and _auth_config_state() == "setup":
        # Explanation: Return this result to the caller; this ends the current function path.
        return RedirectResponse(url="/setup", status_code=303)
    # Explanation: Return this result to the caller; this ends the current function path.
    return _auth_page(False)


@app.post("/api/auth/setup", include_in_schema=False)
# Explanation: Async function create_first_admin: performs asynchronous work; inspect awaited calls and returned result.
async def create_first_admin(request: Request):
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if APP_ENV != "production":
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=404, detail="First-run setup is available only in production mode")
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if DASHBOARD_USERNAME or DASHBOARD_PASSWORD:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=409, detail="Dashboard credentials are controlled by environment variables")
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Assigns or updates a value used later by this function or module.
        payload = await request.json()
        # Explanation: Assigns or updates a value used later by this function or module.
        username = str(payload.get("username", "")).strip()
        # Explanation: Intentional no-op placeholder; this block performs no action.
        password = str(payload.get("password", ""))
    except (ValueError, AttributeError):
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=400, detail="Send a valid JSON username and password")
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if not re.fullmatch(r"[A-Za-z0-9_.@-]{3,64}", username):
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=422, detail="Username must be 3–64 characters using letters, numbers, dot, underscore, @ or hyphen")
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if len(password) < 16 or len(password) > 256 or "\n" in password or "\r" in password:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=422, detail="Password must be 16–256 characters and contain no newline")
    # Explanation: Assigns or updates a value used later by this function or module.
    salt = secrets.token_bytes(16)
    # Explanation: Assigns or updates a value used later by this function or module.
    digest = _password_hash(password, salt)
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Acquire/manage the context resource and release it reliably on exit.
        with _auth_connect() as db:
            # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
            db.execute("INSERT INTO ct_dashboard_auth(id, username, salt, password_hash, created_at) VALUES(1,?,?,?,?)",
                       (username, salt.hex(), digest, int(time.time())))
    except sqlite3.IntegrityError:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=409, detail="Administrator setup has already been completed. Please sign in.")
    except (sqlite3.Error, OSError) as exc:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=503, detail="Could not save administrator account. Check database path and permissions.") from exc
    # Explanation: Assigns or updates a value used later by this function or module.
    response = JSONResponse({"ok": True, "message": "Administrator created"})
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    _issue_session(response, request)
    # Explanation: Return this result to the caller; this ends the current function path.
    return response


@app.post("/api/auth/login", include_in_schema=False)
# Explanation: Async function dashboard_login: performs asynchronous work; inspect awaited calls and returned result.
async def dashboard_login(request: Request):
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Assigns or updates a value used later by this function or module.
        payload = await request.json()
        # Explanation: Assigns or updates a value used later by this function or module.
        username = str(payload.get("username", "")).strip()
        # Explanation: Intentional no-op placeholder; this block performs no action.
        password = str(payload.get("password", ""))
    except (ValueError, AttributeError):
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=400, detail="Send a valid JSON username and password")
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if not _credentials_valid(username, password):
        # Avoid disclosing whether a username exists.
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    # Explanation: Assigns or updates a value used later by this function or module.
    response = JSONResponse({"ok": True})
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    _issue_session(response, request)
    # Explanation: Return this result to the caller; this ends the current function path.
    return response


@app.post("/api/auth/logout", include_in_schema=False)
# Explanation: Function dashboard_logout: implements the operation described by its name and body.
def dashboard_logout(request: Request):
    # Explanation: Assigns or updates a value used later by this function or module.
    token = request.cookies.get(_SESSION_COOKIE, "")
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if token:
        # Explanation: Acquire/manage the context resource and release it reliably on exit.
        with _auth_connect() as db:
            # Explanation: Assigns or updates a value used later by this function or module.
            db.execute("DELETE FROM ct_dashboard_sessions WHERE token_hash=?", (hashlib.sha256(token.encode()).hexdigest(),))
    # Explanation: Assigns or updates a value used later by this function or module.
    response = JSONResponse({"ok": True})
    # Explanation: Assigns or updates a value used later by this function or module.
    response.delete_cookie(_SESSION_COOKIE, path="/")
    # Explanation: Return this result to the caller; this ends the current function path.
    return response

# Explanation: Assigns or updates a value used later by this function or module.
store = Store()
# Explanation: Assigns or updates a value used later by this function or module.
harness = DemoHarness(store)
# Explanation: Sets a module-level constant or configuration value.
TEMPLATE = Path(__file__).parent / "templates" / "index.html"


# Explanation: Class CustomInteraction: groups related data and operations.
class CustomInteraction(BaseModel):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """One examiner-supplied interaction; decoy status is never client supplied."""
    # Explanation: Assigns or updates a value used later by this function or module.
    operation: str = Field(min_length=1, max_length=80)
    # Explanation: Assigns or updates a value used later by this function or module.
    target: str = Field(min_length=1, max_length=250)
    # Explanation: Assigns or updates a value used later by this function or module.
    target_kind: str = Field(default="other", max_length=30)
    # Explanation: Assigns or updates a value used later by this function or module.
    details: str = Field(default="", max_length=500)


# Explanation: Class CustomTestRequest: groups related data and operations.
class CustomTestRequest(BaseModel):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Structured custom test submitted from the dashboard or API."""
    # Explanation: Assigns or updates a value used later by this function or module.
    case_name: str = Field(min_length=1, max_length=100)
    # Explanation: Assigns or updates a value used later by this function or module.
    description: str = Field(default="", max_length=1000)
    # Explanation: Assigns or updates a value used later by this function or module.
    decoy_targets: list[str] = Field(default_factory=list, max_length=100)
    # Explanation: Assigns or updates a value used later by this function or module.
    interactions: list[CustomInteraction] = Field(min_length=1, max_length=100)

# Explanation: Class HTTPGatewayConnectionRequest: groups related data and operations.
class HTTPGatewayConnectionRequest(BaseModel):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Non-secret HTTP gateway configuration submitted from the operator dashboard."""
    # Explanation: Assigns or updates a value used later by this function or module.
    connection_id: str = Field(min_length=1, max_length=64)
    # Explanation: Assigns or updates a value used later by this function or module.
    url: str = Field(min_length=8, max_length=2000)
    # Explanation: Assigns or updates a value used later by this function or module.
    token_env: str = Field(default="", max_length=128)
    # Explanation: Assigns or updates a value used later by this function or module.
    decoy_tools: list[str] = Field(default_factory=list, max_length=100)
    # Explanation: Assigns or updates a value used later by this function or module.
    decoy_resources: list[str] = Field(default_factory=list, max_length=100)
    # Explanation: Assigns or updates a value used later by this function or module.
    decoy_prompts: list[str] = Field(default_factory=list, max_length=100)

@app.get("/", response_class=HTMLResponse, tags=["dashboard"])
# Explanation: Function dashboard: Serve the static dashboard HTML.
def dashboard() -> str:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Serve the static dashboard HTML."""
    # Explanation: Return this result to the caller; this ends the current function path.
    return TEMPLATE.read_text(encoding="utf-8")

@app.get("/health", tags=["system"])
# Explanation: Function health: Public liveness endpoint; deliberately contains no secret/config values.
def health() -> dict:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Public liveness endpoint; deliberately contains no secret/config values."""
    # Explanation: Return this result to the caller; this ends the current function path.
    return {"status": "ok", "service": "MCP-CanaryTrap", "mode": "simulation+MCP-gateway", "environment": APP_ENV}


@app.get("/ready", tags=["system"])
# Explanation: Function readiness: Deployment readiness snapshot. This checks local configuration, not MCP reachability.
def readiness() -> dict:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Deployment readiness snapshot. This checks local configuration, not MCP reachability."""
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    production_auth_configured = _auth_config_state() == "configured"
    # Explanation: Assigns or updates a value used later by this function or module.
    checks = {
        "database_path_configured": bool(os.getenv("CANARYTRAP_DB", "canarytrap.sqlite3")),
        "production_auth_configured": production_auth_configured if APP_ENV == "production" else None,
        "production_mode": APP_ENV == "production",
        "live_mcp_monitoring": True,
        "http_gateway_configured": bool(os.getenv("CANARYTRAP_HTTP_UPSTREAMS", "{}").strip() not in {"", "{}"}),
        "stdio_gateway": "available as a local MCP stdio proxy command",
        "persistent_database_backend": "sqlite",
    }
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    ready = APP_ENV != "production" or production_auth_configured
    # Explanation: Return this result to the caller; this ends the current function path.
    return {"ready": ready, "service": "MCP-CanaryTrap", "checks": checks,
            "note": "Readiness checks configuration only; run end-to-end transport tests before production use."}

@app.post("/api/gateway/connections", tags=["live MCP gateway"])
# Explanation: Function save_gateway_connection: Save non-secret HTTP upstream settings to the local persistent configuration store.
def save_gateway_connection(request: HTTPGatewayConnectionRequest, ctx=Depends(_actor_context)) -> dict:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Save non-secret HTTP upstream settings to the local persistent configuration store."""
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    _require(ctx, {"admin", "operator"})
    # Explanation: Assigns or updates a value used later by this function or module.
    connection_id = request.connection_id.strip()
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if not re.fullmatch(r"[A-Za-z0-9_-]+", connection_id):
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=422, detail="Connection ID may contain letters, numbers, underscores, and hyphens only")
    # Explanation: Assigns or updates a value used later by this function or module.
    url = request.url.strip()
    # Explanation: Assigns or updates a value used later by this function or module.
    parsed_url = urlsplit(url)
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if parsed_url.scheme not in {"https", "http"} or not parsed_url.hostname:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=422, detail="Upstream URL must be a valid http:// or https:// URL")
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if parsed_url.username or parsed_url.password:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=422, detail="Do not embed username/password credentials in the upstream URL")
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        validate_upstream_url(url)
    except ValueError as exc:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    # Explanation: Assigns or updates a value used later by this function or module.
    token_env = request.token_env.strip()
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if token_env and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", token_env):
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=422, detail="token_env must be a valid environment-variable name")
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if token_env and APP_ENV == "production" and parsed_url.scheme != "https":
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=422, detail="Use an HTTPS upstream URL when configuring a bearer token in production")
    # Explanation: Assigns or updates a value used later by this function or module.
    decoys = {
        "decoy_tools": [x.strip() for x in request.decoy_tools if x.strip()],
        "decoy_resources": [x.strip() for x in request.decoy_resources if x.strip()],
        "decoy_prompts": [x.strip() for x in request.decoy_prompts if x.strip()],
    }
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if not any(decoys.values()):
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=422, detail="Configure at least one decoy tool, resource, or prompt")
    # Explanation: Loop over each item in the iterable and run the indented body.
    for kind, values in decoys.items():
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        if len(values) != len(set(values)):
            # Explanation: Raise an exception to reject the operation or report a failure.
            raise HTTPException(status_code=422, detail=f"Duplicate values in {kind}")
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        if any(len(value) > 250 for value in values):
            # Explanation: Raise an exception to reject the operation or report a failure.
            raise HTTPException(status_code=422, detail=f"Values in {kind} must be 250 characters or fewer")
    # Explanation: Assigns or updates a value used later by this function or module.
    connection = {"id": connection_id, "url": url, "token_env": token_env, **decoys}
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    store.save_gateway_connection(connection)
    # Explanation: Return this result to the caller; this ends the current function path.
    return {
        "saved": True,
        "connection": {
            "id": connection_id, "url": url, "token_env": token_env,
            **decoys, "token_configured": bool(token_env and os.getenv(token_env, "")),
            "endpoint": f"/gateway/{connection_id}",
        },
        "secrets_stored": False,
        "note": "Configuration is active immediately. If token_env is set, add that secret to the server environment before connecting."
    }


@app.delete("/api/gateway/connections/{connection_id}", tags=["live MCP gateway"])
# Explanation: Function delete_gateway_connection: Delete a dashboard-saved connection; environment-defined connections remain active.
def delete_gateway_connection(connection_id: str, ctx=Depends(_actor_context)) -> dict:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Delete a dashboard-saved connection; environment-defined connections remain active."""
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    _require(ctx, {"admin"})
    # Explanation: Assigns or updates a value used later by this function or module.
    deleted = store.delete_gateway_connection(connection_id)
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if not deleted:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=404, detail="No dashboard-saved connection with that ID")
    # Explanation: Return this result to the caller; this ends the current function path.
    return {"deleted": True, "connection_id": connection_id}


@app.post("/api/gateway/connections/{connection_id}/test", tags=["live MCP gateway"])
# Explanation: Async function test_gateway_connection: performs asynchronous work; inspect awaited calls and returned result.
async def test_gateway_connection(connection_id: str, ctx=Depends(_actor_context)) -> dict:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Send an MCP initialize request to verify reachability and protocol response."""
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    _require(ctx, {"admin", "operator"})
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Assigns or updates a value used later by this function or module.
        config = load_http_upstreams().get(connection_id)
    except ValueError as exc:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if not config:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=404, detail="Connection is not configured")
    # Explanation: Assigns or updates a value used later by this function or module.
    headers = {"accept": "application/json, text/event-stream", "content-type": "application/json"}
    # Explanation: Assigns or updates a value used later by this function or module.
    token_env = str(config.get("token_env") or "")
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if token_env:
        # Explanation: Assigns or updates a value used later by this function or module.
        token = os.getenv(token_env, "")
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        if not token:
            # Explanation: Raise an exception to reject the operation or report a failure.
            raise HTTPException(status_code=503, detail=f"Configured credential environment variable '{token_env}' is not set")
        # Explanation: Assigns or updates a value used later by this function or module.
        headers["authorization"] = f"Bearer {token}"
    # Explanation: Assigns or updates a value used later by this function or module.
    payload = {"jsonrpc": "2.0", "id": "canarytrap-init-check", "method": "initialize", "params": {
        "protocolVersion": "2025-03-26", "capabilities": {},
        "clientInfo": {"name": "MCP-CanaryTrap", "version": "1.3.0"}
    }}
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Asynchronously manage a resource and ensure its cleanup.
        async with httpx.AsyncClient(timeout=httpx.Timeout(12.0, connect=5.0), follow_redirects=False) as client:
            # Explanation: Assigns or updates a value used later by this function or module.
            response = await client.post(config["url"], json=payload, headers=headers)
            # Explanation: Conditional decision: execute the following branch only when this expression is true.
            if response.status_code >= 400:
                # Explanation: Raise an exception to reject the operation or report a failure.
                raise HTTPException(status_code=502, detail=f"Upstream returned HTTP {response.status_code}")
            # Explanation: Assigns or updates a value used later by this function or module.
            result_payload = None
            # Explanation: Conditional decision: execute the following branch only when this expression is true.
            if "application/json" in response.headers.get("content-type", ""):
                # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
                try:
                    # Explanation: Assigns or updates a value used later by this function or module.
                    result_payload = response.json()
                except ValueError:
                    # Explanation: Assigns or updates a value used later by this function or module.
                    result_payload = None
            # Explanation: Conditional decision: execute the following branch only when this expression is true.
            elif "text/event-stream" in response.headers.get("content-type", ""):
                # Explanation: Loop over each item in the iterable and run the indented body.
                for line in response.text.splitlines():
                    # Explanation: Conditional decision: execute the following branch only when this expression is true.
                    if line.startswith("data:"):
                        # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
                        try:
                            # Explanation: Assigns or updates a value used later by this function or module.
                            result_payload = json.loads(line[5:].strip())
                            # Explanation: Stops the nearest enclosing loop immediately.
                            break
                        except json.JSONDecodeError:
                            # Explanation: Skips the rest of this loop iteration and proceeds to the next iteration.
                            continue
            # Explanation: Assigns or updates a value used later by this function or module.
            result = result_payload.get("result") if isinstance(result_payload, dict) else None
            # Explanation: Conditional decision: execute the following branch only when this expression is true.
            if not isinstance(result, dict) or not result.get("protocolVersion"):
                # Explanation: Raise an exception to reject the operation or report a failure.
                raise HTTPException(status_code=502, detail="Upstream did not return a valid MCP initialize result")
            # Explanation: Assigns or updates a value used later by this function or module.
            session_id = response.headers.get("mcp-session-id")
            # Explanation: Conditional decision: execute the following branch only when this expression is true.
            if session_id:
                # Explanation: Assigns or updates a value used later by this function or module.
                session_headers = {**headers, "mcp-session-id": session_id, "mcp-protocol-version": result.get("protocolVersion", "2025-03-26")}
                # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
                try:
                    # Explanation: Waits for an asynchronous operation to complete and obtains its result.
                    await client.post(config["url"], json={"jsonrpc": "2.0", "method": "notifications/initialized"}, headers=session_headers)
                    # Explanation: Waits for an asynchronous operation to complete and obtains its result.
                    await client.delete(config["url"], headers=session_headers)
                except httpx.HTTPError:
                    # Explanation: Intentional no-op placeholder; this block performs no action.
                    pass
            # Explanation: Assigns or updates a value used later by this function or module.
            server_info = result.get("serverInfo") if isinstance(result.get("serverInfo"), dict) else {}
            # Explanation: Return this result to the caller; this ends the current function path.
            return {"connected": True, "connection_id": connection_id,
                    "protocol_version": result.get("protocolVersion"),
                    "server_name": server_info.get("name", "unknown"),
                    "server_version": server_info.get("version", "unknown"),
                    "note": "Initialize handshake succeeded. This is a connectivity check, not a security certification."}
    except HTTPException:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise
    except httpx.TimeoutException as exc:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=504, detail="Upstream MCP initialize timed out") from exc
    except httpx.HTTPError as exc:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=502, detail=f"Could not connect to upstream MCP server: {type(exc).__name__}") from exc


@app.get("/api/gateway/config", tags=["live MCP gateway"])
# Explanation: Function gateway_config_status: Return non-secret gateway configuration status for the dashboard.
def gateway_config_status(ctx=Depends(_actor_context)) -> dict:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Return non-secret gateway configuration status for the dashboard."""
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    _require(ctx, {"admin", "operator"})
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Assigns or updates a value used later by this function or module.
        upstreams = load_http_upstreams()
    except ValueError as exc:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    # Explanation: Return this result to the caller; this ends the current function path.
    return {
        "http_connections": [
            {"id": connection_id, "url": cfg["url"],
             "decoy_tools": len(cfg["decoy_tools"]),
             "decoy_resources": len(cfg["decoy_resources"]),
             "decoy_prompts": len(cfg["decoy_prompts"]),
             "token_configured": bool(cfg["token_env"] and os.getenv(str(cfg["token_env"]), ""))}
            for connection_id, cfg in upstreams.items()
        ],
        "stdio_proxy_available": True,
        "secrets_returned": False,
        "note": "This reports configured adapters only; it does not prove upstream connectivity or certify production readiness."
    }


@app.get("/api/sessions", tags=["sessions"])
# Explanation: Function sessions: List persisted test sessions for the authenticated tenant.
def sessions(ctx=Depends(_actor_context)) -> list[dict]:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """List persisted test sessions for the authenticated tenant."""
    # Explanation: Return this result to the caller; this ends the current function path.
    return store.list_sessions(tenant=ctx["tenant"])

@app.get("/api/events", tags=["events"])
# Explanation: Function events: List recent events restricted to the authenticated tenant.
def events(session_id: str | None = Query(default=None), ctx=Depends(_actor_context)) -> list[dict]:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """List recent events restricted to the authenticated tenant."""
    # Explanation: Return this result to the caller; this ends the current function path.
    return store.list_events(session_id, tenant=ctx["tenant"])

@app.post("/api/demo/{scenario}", tags=["demo"])
# Explanation: Function run_demo: Run a benign or overreaching simulation in the authenticated tenant.
def run_demo(scenario: str, ctx=Depends(_actor_context)) -> dict:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Run a benign or overreaching simulation in the authenticated tenant."""
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if scenario not in {"benign", "overreaching"}:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=400, detail="scenario must be benign or overreaching")
    # Explanation: Return this result to the caller; this ends the current function path.
    return harness.run(scenario, tenant=ctx["tenant"])


@app.post("/api/custom-test", tags=["custom tests"])
# Explanation: Function run_custom_test: Evaluate a user-defined case within the authenticated tenant.
def run_custom_test(request: CustomTestRequest, ctx=Depends(_actor_context)) -> dict:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Evaluate a user-defined case within the authenticated tenant."""
    # Explanation: Assigns or updates a value used later by this function or module.
    decoys = [target.strip() for target in request.decoy_targets if target.strip()]
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if len({target.casefold() for target in decoys}) != len(decoys):
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=422, detail="decoy targets must be unique (case-insensitive)")
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Return this result to the caller; this ends the current function path.
        return harness.run_custom(
            case_name=request.case_name,
            description=request.description,
            decoy_targets=decoys,
            interactions=[item.model_dump() for item in request.interactions],
            tenant=ctx["tenant"],
        )
    except ValueError as exc:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=422, detail=str(exc)) from exc

# Explanation: Function run: Start the server; hosted platforms supply HOST/PORT through environment variables.
def run() -> None:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Start the server; hosted platforms supply HOST/PORT through environment variables."""
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    host = os.getenv("HOST", "127.0.0.1" if APP_ENV != "production" else "0.0.0.0")
    # Explanation: Assigns or updates a value used later by this function or module.
    port = int(os.getenv("PORT", "8000"))
    # Explanation: Assigns or updates a value used later by this function or module.
    uvicorn.run("mcp_canarytrap.api:app", host=host, port=port, reload=False)

# Explanation: Conditional decision: execute the following branch only when this expression is true.
if __name__ == "__main__":
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    run()
