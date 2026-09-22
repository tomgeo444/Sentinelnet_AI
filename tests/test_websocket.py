"""
Integration tests for WebSocket communication.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_websocket_stream():
    with client.websocket_connect("/ws") as websocket:
        # Initial message
        init_data = websocket.receive_json()
        assert init_data["type"] == "INITIAL_STATE"
        assert "status" in init_data["data"]
        assert "statistics" in init_data["data"]

        # Ping pong test
        websocket.send_text("ping")
        resp = websocket.receive_text()
        assert resp == "pong"
