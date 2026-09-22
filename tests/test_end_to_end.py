"""
End-to-end integration test verifying the complete pipeline:
Packet -> Flow Aggregation -> Feature Extraction -> Deep Learning Inference -> Risk Engine -> Database Logging.
"""

import time
import pytest
from capture.flow_manager import FlowManager
from backend.services.monitor_service import monitor_service
from database.database import session_scope
from database.models import Detection


def test_end_to_end_flow_detection_pipeline():
    # 1. Setup Flow Manager with monitor_service callback
    flow_mgr = FlowManager(idle_timeout=0.1, active_timeout=1.0, on_flow_complete=monitor_service._on_flow_completed)

    # 2. Simulate PortScan probe packet flow
    src_ip = "192.168.1.150"
    dst_ip = "192.168.1.1"
    sport = 49152
    dport = 8080

    flow_mgr.process_packet(
        src_ip=src_ip,
        dst_ip=dst_ip,
        src_port=sport,
        dst_port=dport,
        protocol_name="TCP",
        protocol_num=6,
        length=54,
        timestamp=time.time(),
        tcp_flags={"syn": 1},
    )

    # 3. Flush expired flow
    time.sleep(0.15)
    flow_mgr.flush_expired_flows()

    # 4. Verify detection was processed and recorded in recent detections
    recent = monitor_service.get_recent_detections(limit=10)
    assert len(recent) > 0

    found_det = next((d for d in recent if d["source_ip"] == src_ip and d["destination_port"] == dport), None)
    assert found_det is not None
    assert "prediction" in found_det
    assert "confidence" in found_det
    assert "risk_level" in found_det

    # 5. Verify detection persisted in SQLite/MariaDB
    with session_scope() as session:
        db_record = session.query(Detection).filter_by(source_ip=src_ip, destination_port=dport).first()
        assert db_record is not None
        assert db_record.protocol == "TCP"
