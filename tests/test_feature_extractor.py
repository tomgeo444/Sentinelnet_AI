"""
Unit tests for Feature Extractor and Flow Aggregator.
"""

import pytest
import numpy as np
from capture.feature_extractor import (
    extract_features_from_flow,
    feature_dict_to_vector,
    calculate_mean_std,
    calculate_iats,
    FEATURE_COLUMNS,
)
from capture.flow_manager import FlowManager


def test_calculate_mean_std():
    mean, std = calculate_mean_std([10.0, 20.0, 30.0])
    assert mean == pytest.approx(20.0, 0.001)
    assert std > 0

    mean_single, std_single = calculate_mean_std([100.0])
    assert mean_single == 100.0
    assert std_single == 0.0

    mean_empty, std_empty = calculate_mean_std([])
    assert mean_empty == 0.0
    assert std_empty == 0.0


def test_calculate_iats():
    timestamps = [1.0, 1.2, 1.5, 2.0]
    iats = calculate_iats(timestamps)
    assert len(iats) == 3
    assert iats[0] == pytest.approx(0.2, 0.001)
    assert iats[1] == pytest.approx(0.3, 0.001)
    assert iats[2] == pytest.approx(0.5, 0.001)


def test_extract_features_from_flow():
    dummy_flow = {
        "start_time": 1000.0,
        "last_time": 1002.5,
        "protocol_num": 6,
        "fwd_packet_lengths": [64, 128, 256],
        "bwd_packet_lengths": [1024, 512],
        "fwd_timestamps": [1000.0, 1001.0, 1002.0],
        "bwd_timestamps": [1000.5, 1001.5],
        "all_timestamps": [1000.0, 1000.5, 1001.0, 1001.5, 1002.0],
        "flags": {"syn": 1, "ack": 4, "psh": 2, "fin": 1, "rst": 0},
    }

    features = extract_features_from_flow(dummy_flow)

    assert len(features) == len(FEATURE_COLUMNS)
    assert features["total_fwd_packets"] == 3
    assert features["total_bwd_packets"] == 2
    assert features["total_fwd_bytes"] == 64 + 128 + 256
    assert features["syn_flag_count"] == 1
    assert features["ack_flag_count"] == 4
    assert features["protocol_num"] == 6
    assert features["flow_duration"] == pytest.approx(2.5, 0.001)

    # Test vector conversion
    vec = feature_dict_to_vector(features)
    assert isinstance(vec, np.ndarray)
    assert len(vec) == 22
    assert not np.isnan(vec).any()


def test_flow_manager_aggregation():
    emitted_flows = []

    def on_flow(payload):
        emitted_flows.append(payload)

    mgr = FlowManager(idle_timeout=0.2, active_timeout=1.0, on_flow_complete=on_flow)

    # Ingest 3 packets for Flow A
    mgr.process_packet(
        src_ip="192.168.1.10",
        dst_ip="10.0.0.1",
        src_port=50000,
        dst_port=80,
        protocol_name="TCP",
        protocol_num=6,
        length=60,
        timestamp=100.0,
        tcp_flags={"syn": 1},
    )
    mgr.process_packet(
        src_ip="10.0.0.1",
        dst_ip="192.168.1.10",
        src_port=80,
        dst_port=50000,
        protocol_name="TCP",
        protocol_num=6,
        length=60,
        timestamp=100.1,
        tcp_flags={"syn": 1, "ack": 1},
    )
    # Terminate with FIN
    mgr.process_packet(
        src_ip="192.168.1.10",
        dst_ip="10.0.0.1",
        src_port=50000,
        dst_port=80,
        protocol_name="TCP",
        protocol_num=6,
        length=40,
        timestamp=100.2,
        tcp_flags={"fin": 1, "ack": 1},
    )

    assert len(emitted_flows) == 1
    flow_res = emitted_flows[0]
    assert flow_res["source_ip"] == "192.168.1.10"
    assert flow_res["destination_ip"] == "10.0.0.1"
    assert flow_res["packet_count"] == 3
    assert flow_res["features"]["syn_flag_count"] == 2
