"""Checks for the minimal production-mode access guard and health endpoints."""
import base64
from fastapi.testclient import TestClient
from mcp_canarytrap import api


def test_production_routes_require_basic_auth(monkeypatch):
    monkeypatch.setattr(api, "APP_ENV", "production")
    monkeypatch.setattr(api, "DASHBOARD_USERNAME", "operator")
    monkeypatch.setattr(api, "DASHBOARD_PASSWORD", "a-very-long-test-password")
    client = TestClient(api.app)
    assert client.get("/").status_code == 401
    assert client.get("/api/sessions").status_code == 401
    assert client.get("/health").status_code == 200


def test_production_routes_accept_valid_basic_auth(monkeypatch):
    monkeypatch.setattr(api, "APP_ENV", "production")
    monkeypatch.setattr(api, "DASHBOARD_USERNAME", "operator")
    monkeypatch.setattr(api, "DASHBOARD_PASSWORD", "a-very-long-test-password")
    token = base64.b64encode(b"operator:a-very-long-test-password").decode("ascii")
    client = TestClient(api.app, headers={"Authorization": f"Basic {token}"})
    response = client.get("/")
    assert response.status_code == 200
    assert "Setup & Deploy Wizard" in response.text
    assert response.headers["x-content-type-options"] == "nosniff"


def test_production_mode_fails_closed_without_credentials(monkeypatch):
    monkeypatch.setattr(api, "APP_ENV", "production")
    monkeypatch.setattr(api, "DASHBOARD_USERNAME", "")
    monkeypatch.setattr(api, "DASHBOARD_PASSWORD", "")
    client = TestClient(api.app)
    response = client.get("/")
    assert response.status_code == 503
    assert client.get("/ready").json()["ready"] is False
