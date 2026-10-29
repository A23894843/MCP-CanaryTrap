# Annotated source file for MCP-CanaryTrap v1.3.2.
# Lines beginning with "Explanation:" describe the following statement or branch.
# Original executable statements are preserved; comments are for learning.

# Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
"""Production dashboard setup, login and access-guard regression tests."""
# Explanation: Imports modules that this file uses.
import base64
# Explanation: Imports names from fastapi.testclient.
from fastapi.testclient import TestClient
# Explanation: Imports names from mcp_canarytrap.
from mcp_canarytrap import api


# Explanation: Function configure_auth: implements the operation described by its name and body.
def configure_auth(monkeypatch, tmp_path, username="", password=""):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setattr(api, "APP_ENV", "production")
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setattr(api, "DASHBOARD_USERNAME", username)
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setattr(api, "DASHBOARD_PASSWORD", password)
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    monkeypatch.setenv("CANARYTRAP_DB", str(tmp_path / "auth-test.sqlite3"))


# Explanation: Function test_production_routes_require_auth_and_browser_gets_login_form: implements the operation described by its name and body.
def test_production_routes_require_auth_and_browser_gets_login_form(monkeypatch, tmp_path):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    configure_auth(monkeypatch, tmp_path, "operator", "a-very-long-test-password")
    # Explanation: Assigns or updates a value used later by this function or module.
    client = TestClient(api.app)
    # Explanation: Assigns or updates a value used later by this function or module.
    page = client.get("/")
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert page.status_code == 200
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert "Sign in" in page.text
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert client.get("/api/sessions").status_code == 401
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert client.get("/health").status_code == 200


# Explanation: Function test_production_routes_accept_valid_basic_auth: implements the operation described by its name and body.
def test_production_routes_accept_valid_basic_auth(monkeypatch, tmp_path):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    configure_auth(monkeypatch, tmp_path, "operator", "a-very-long-test-password")
    # Explanation: Assigns or updates a value used later by this function or module.
    token = base64.b64encode(b"operator:a-very-long-test-password").decode("ascii")
    # Explanation: Assigns or updates a value used later by this function or module.
    client = TestClient(api.app, headers={"Authorization": f"Basic {token}"})
    # Explanation: Assigns or updates a value used later by this function or module.
    response = client.get("/")
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert response.status_code == 200
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert "Settings & Deployment" in response.text
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert response.headers["x-content-type-options"] == "nosniff"


# Explanation: Function test_first_run_setup_creates_admin_and_protects_dashboard: implements the operation described by its name and body.
def test_first_run_setup_creates_admin_and_protects_dashboard(monkeypatch, tmp_path):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    configure_auth(monkeypatch, tmp_path)
    # Explanation: Assigns or updates a value used later by this function or module.
    client = TestClient(api.app)
    # Explanation: Assigns or updates a value used later by this function or module.
    first_page = client.get("/")
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert first_page.status_code == 200
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert "Administrator setup" in first_page.text
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert client.get("/ready").json()["ready"] is False

    # Explanation: Assigns or updates a value used later by this function or module.
    response = client.post("/api/auth/setup", json={
        "username": "canary-admin",
        "password": "a-unique-password-for-testing",
    })
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert response.status_code == 200
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert response.json()["ok"] is True
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert response.cookies.get("canarytrap_session")
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert "Settings & Deployment" in client.get("/").text
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert client.get("/ready").json()["ready"] is True

    # Explanation: Assigns or updates a value used later by this function or module.
    second_setup = client.post("/api/auth/setup", json={
        "username": "another-admin",
        "password": "another-unique-password-for-test",
    })
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert second_setup.status_code == 409


# Explanation: Function test_login_and_logout_with_database_account: implements the operation described by its name and body.
def test_login_and_logout_with_database_account(monkeypatch, tmp_path):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    configure_auth(monkeypatch, tmp_path)
    # Explanation: Assigns or updates a value used later by this function or module.
    client = TestClient(api.app)
    # Explanation: Assigns or updates a value used later by this function or module.
    response = client.post("/api/auth/setup", json={
        "username": "operator",
        "password": "a-unique-password-for-testing",
    })
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert response.status_code == 200
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    client.post("/api/auth/logout")
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert "Sign in" in client.get("/").text

    # Explanation: Assigns or updates a value used later by this function or module.
    login = client.post("/api/auth/login", json={
        "username": "operator",
        "password": "a-unique-password-for-testing",
    })
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert login.status_code == 200
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert "Settings & Deployment" in client.get("/").text

    # Explanation: Assigns or updates a value used later by this function or module.
    bad_login = TestClient(api.app).post("/api/auth/login", json={
        "username": "operator",
        "password": "wrong-password",
    })
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert bad_login.status_code == 401


# Explanation: Function test_first_run_setup_rejects_weak_password: implements the operation described by its name and body.
def test_first_run_setup_rejects_weak_password(monkeypatch, tmp_path):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    configure_auth(monkeypatch, tmp_path)
    # Explanation: Assigns or updates a value used later by this function or module.
    response = TestClient(api.app).post("/api/auth/setup", json={
        "username": "admin",
        "password": "short",
    })
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert response.status_code == 422


# Explanation: Function test_production_mode_fails_closed_when_environment_credentials_are_partial: implements the operation described by its name and body.
def test_production_mode_fails_closed_when_environment_credentials_are_partial(monkeypatch, tmp_path):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    configure_auth(monkeypatch, tmp_path, "operator", "")
    # Explanation: Assigns or updates a value used later by this function or module.
    client = TestClient(api.app)
    # Explanation: Assigns or updates a value used later by this function or module.
    response = client.get("/api/sessions")
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert response.status_code == 503
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert "Set both DASHBOARD_USERNAME" in response.json()["detail"]
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert client.get("/ready").json()["ready"] is False


# Explanation: Function test_password_is_stored_as_a_hash_not_plaintext: implements the operation described by its name and body.
def test_password_is_stored_as_a_hash_not_plaintext(monkeypatch, tmp_path):
    # Explanation: Imports modules that this file uses.
    import sqlite3
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    configure_auth(monkeypatch, tmp_path)
    # Explanation: Intentional no-op placeholder; this block performs no action.
    password = "a-unique-password-for-testing"
    # Explanation: Assigns or updates a value used later by this function or module.
    response = TestClient(api.app).post("/api/auth/setup", json={
        "username": "operator",
        "password": password,
    })
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert response.status_code == 200
    # Explanation: Acquire/manage the context resource and release it reliably on exit.
    with sqlite3.connect(tmp_path / "auth-test.sqlite3") as db:
        # Explanation: Assigns or updates a value used later by this function or module.
        row = db.execute("SELECT salt, password_hash FROM ct_dashboard_auth WHERE id=1").fetchone()
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert row is not None
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert password not in row[1]
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert len(row[1]) == 64
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert len(row[0]) == 32
