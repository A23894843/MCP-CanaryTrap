"""First-run password setup and session authentication for the local dashboard."""
from pathlib import Path
import hashlib
import hmac
import json
import os
import secrets

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
AUTH_FILE = DATA / "auth.json"
SECRET_FILE = DATA / ".session_secret"
router = APIRouter()

def _ensure_secret() -> str:
    DATA.mkdir(parents=True, exist_ok=True)
    if not SECRET_FILE.exists():
        SECRET_FILE.write_text(secrets.token_urlsafe(48))
        try:
            SECRET_FILE.chmod(0o600)
        except OSError:
            pass
    return SECRET_FILE.read_text().strip()

SESSION_SECRET = os.environ.get("MCP_CANARYTRAP_SESSION_SECRET") or _ensure_secret()

def password_configured() -> bool:
    return AUTH_FILE.exists()

def _hash_password(password: str, salt: bytes | None = None) -> dict:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 310_000)
    return {"salt": salt.hex(), "hash": digest.hex(), "iterations": 310_000}

def _verify_password(password: str) -> bool:
    try:
        config = json.loads(AUTH_FILE.read_text())
        salt = bytes.fromhex(config["salt"])
        expected = bytes.fromhex(config["hash"])
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(config["iterations"]))
        return hmac.compare_digest(actual, expected)
    except (OSError, ValueError, KeyError, TypeError):
        return False

def _page(title: str, message: str, action: str, button: str, confirm: bool = False) -> str:
    confirm_field = ('<label>Confirm password</label><input name="confirm_password" type="password" minlength="12" required autocomplete="new-password">'
                     if confirm else "")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} | MCP-CanaryTrap</title><link rel="stylesheet" href="/static/css/style.css"></head><body class="auth-body"><main class="auth-card"><p class="eyebrow">MCP SECURITY ASSESSMENT SUITE</p><h1>MCP-CanaryTrap</h1><h2>{title}</h2><p>{message}</p><form method="post" action="{action}"><label>Password</label><input name="password" type="password" minlength="12" required autocomplete="{'new-password' if confirm else 'current-password'}">{confirm_field}<button type="submit">{button}</button></form><small>Use a unique password with at least 12 characters. The password is stored as a salted PBKDF2 hash, never as plain text.</small></main></body></html>"""

@router.get("/setup", response_class=HTMLResponse)
def setup_page():
    if password_configured():
        return RedirectResponse("/login", status_code=303)
    return _page("Set your administrator password", "First-time setup. Create the password used for all future sign-ins.", "/auth/setup", "Save password", True)

@router.get("/login", response_class=HTMLResponse)
def login_page():
    if not password_configured():
        return RedirectResponse("/setup", status_code=303)
    return _page("Sign in", "Enter your administrator password to access the security dashboard.", "/auth/login", "Sign in")

@router.post("/auth/setup", response_class=HTMLResponse)
def setup_password(request: Request, password: str = Form(...), confirm_password: str = Form(...)):
    if password_configured():
        return RedirectResponse("/login", status_code=303)
    if len(password) < 12 or password != confirm_password:
        return HTMLResponse(_page("Password setup", "Passwords must match and contain at least 12 characters. Try again.", "/auth/setup", "Save password", True), status_code=400)
    DATA.mkdir(parents=True, exist_ok=True)
    temp = AUTH_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps(_hash_password(password)))
    try:
        temp.chmod(0o600)
    except OSError:
        pass
    temp.replace(AUTH_FILE)
    request.session.clear()
    request.session["authenticated"] = True
    return RedirectResponse("/dashboard", status_code=303)

@router.post("/auth/login", response_class=HTMLResponse)
def login(request: Request, password: str = Form(...)):
    if not password_configured():
        return RedirectResponse("/setup", status_code=303)
    if not _verify_password(password):
        return HTMLResponse(_page("Sign in", "Incorrect password. Please try again.", "/auth/login", "Sign in"), status_code=401)
    request.session.clear()
    request.session["authenticated"] = True
    return RedirectResponse("/dashboard", status_code=303)

@router.post("/auth/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
