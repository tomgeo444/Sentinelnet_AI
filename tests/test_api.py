"""
Integration tests for FastAPI REST endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ONLINE"
    assert "database" in data
    assert "monitoring" in data


def test_interfaces_endpoint():
    response = client.get("/api/interfaces")
    assert response.status_code == 200
    data = response.json()
    assert "interfaces" in data
    assert isinstance(data["interfaces"], list)


def test_model_info_endpoint():
    response = client.get("/api/model/info")
    assert response.status_code == 200
    data = response.json()
    assert "architecture" in data
    assert "features_count" in data


def test_statistics_endpoint():
    response = client.get("/api/statistics")
    assert response.status_code == 200
    data = response.json()
    assert "packets_captured" in data
    assert "flows_processed" in data
    assert "system_metrics" in data


def test_monitoring_start_stop():
    start_resp = client.post("/api/monitoring/start", json={"interface": "lo"})
    assert start_resp.status_code == 200
    assert start_resp.json()["status"] in ("STARTED", "ALREADY_RUNNING")

    status_resp = client.get("/api/monitoring/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["monitoring_active"] is True

    stop_resp = client.post("/api/monitoring/stop")
    assert stop_resp.status_code == 200
    assert stop_resp.json()["status"] == "STOPPED"
