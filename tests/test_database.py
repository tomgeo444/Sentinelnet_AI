"""
Unit tests for Database Operations and SQLAlchemy models.
"""

import pytest
from datetime import datetime
from database.database import init_db, session_scope, get_database_status
from database.models import Detection, SystemMetric, MonitoringSession


def test_database_initialization_and_status():
    engine = init_db()
    assert engine is not None
    status = get_database_status()
    assert status["status"] == "CONNECTED"


def test_detection_crud_operations():
    with session_scope() as session:
        detection = Detection(
            source_ip="192.168.1.100",
            destination_ip="10.0.0.5",
            source_port=44332,
            destination_port=80,
            protocol="TCP",
            prediction="DoS_DDoS",
            attack_type="DoS_DDoS",
            is_attack=True,
            confidence=0.982,
            risk_level="CRITICAL",
            flow_duration=1.23,
            packet_count=150,
            byte_count=12000,
        )
        session.add(detection)
        session.flush()

        det_id = detection.id
        assert det_id is not None

    # Query back
    with session_scope() as session:
        retrieved = session.query(Detection).filter_by(id=det_id).first()
        assert retrieved is not None
        assert retrieved.prediction == "DoS_DDoS"
        assert retrieved.is_attack is True
        assert retrieved.risk_level == "CRITICAL"
        d_dict = retrieved.to_dict()
        assert d_dict["id"] == det_id
        assert d_dict["confidence"] == 0.982
