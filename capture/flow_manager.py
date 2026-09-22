"""
SentinelNet AI - Real-Time Bidirectional Flow Aggregation Engine
Groups raw network packets into bidirectional 5-tuple flows with timeout management.
"""

import time
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from capture.feature_extractor import extract_features_from_flow

logger = logging.getLogger("sentinelnet.flow_manager")


@dataclass
class FlowRecord:
    """Represents a bidirectional network conversation between two endpoints."""
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol_name: str
    protocol_num: int
    start_time: float
    last_time: float
    fwd_src_ip: str
    fwd_src_port: int

    fwd_packet_lengths: list[int] = field(default_factory=list)
    bwd_packet_lengths: list[int] = field(default_factory=list)
    fwd_timestamps: list[float] = field(default_factory=list)
    bwd_timestamps: list[float] = field(default_factory=list)
    all_timestamps: list[float] = field(default_factory=list)
    flags: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    packet_count: int = 0
    byte_count: int = 0
    is_closed: bool = False

    def add_packet(self, src_ip: str, src_port: int, length: int, timestamp: float, tcp_flags: dict = None):
        """Appends a packet to the flow record with directional assignment."""
        self.last_time = timestamp
        self.packet_count += 1
        self.byte_count += length
        self.all_timestamps.append(timestamp)

        is_fwd = (src_ip == self.fwd_src_ip and src_port == self.fwd_src_port)
        if is_fwd:
            self.fwd_packet_lengths.append(length)
            self.fwd_timestamps.append(timestamp)
        else:
            self.bwd_packet_lengths.append(length)
            self.bwd_timestamps.append(timestamp)

        if tcp_flags:
            for flag, count in tcp_flags.items():
                self.flags[flag] += count
            if tcp_flags.get("fin", 0) > 0 or tcp_flags.get("rst", 0) > 0:
                self.is_closed = True

    def to_feature_payload(self) -> dict:
        """Converts flow to a dictionary ready for feature extraction."""
        flow_dict = {
            "start_time": self.start_time,
            "last_time": self.last_time,
            "protocol_num": self.protocol_num,
            "fwd_packet_lengths": self.fwd_packet_lengths,
            "bwd_packet_lengths": self.bwd_packet_lengths,
            "fwd_timestamps": self.fwd_timestamps,
            "bwd_timestamps": self.bwd_timestamps,
            "all_timestamps": self.all_timestamps,
            "flags": dict(self.flags),
        }
        features = extract_features_from_flow(flow_dict)
        return {
            "source_ip": self.fwd_src_ip,
            "destination_ip": self.dst_ip if self.src_ip == self.fwd_src_ip else self.src_ip,
            "source_port": self.fwd_src_port,
            "destination_port": self.dst_port if self.src_port == self.fwd_src_port else self.src_port,
            "protocol": self.protocol_name,
            "protocol_num": self.protocol_num,
            "start_time": self.start_time,
            "last_time": self.last_time,
            "duration": round(max(0.0001, self.last_time - self.start_time), 4),
            "packet_count": self.packet_count,
            "byte_count": self.byte_count,
            "features": features,
        }


class FlowManager:
    """
    Thread-safe bidirectional flow state tracker and timeout manager.
    """
    def __init__(self, idle_timeout: float = 2.0, active_timeout: float = 10.0, on_flow_complete=None):
        self.idle_timeout = idle_timeout
        self.active_timeout = active_timeout
        self.on_flow_complete = on_flow_complete
        self.active_flows: dict[tuple, FlowRecord] = {}

    def _canonical_key(self, src_ip: str, dst_ip: str, src_port: int, dst_port: int, proto: str) -> tuple:
        """Generates a canonical bidirectional flow identifier."""
        if (src_ip, src_port) < (dst_ip, dst_port):
            return (src_ip, dst_ip, src_port, dst_port, proto)
        return (dst_ip, src_ip, dst_port, src_port, proto)

    def process_packet(
        self,
        src_ip: str,
        dst_ip: str,
        src_port: int,
        dst_port: int,
        protocol_name: str,
        protocol_num: int,
        length: int,
        timestamp: float = None,
        tcp_flags: dict = None,
    ):
        """Ingests a packet and updates active flow state."""
        ts = timestamp if timestamp is not None else time.time()
        key = self._canonical_key(src_ip, dst_ip, src_port, dst_port, protocol_name)

        flow = self.active_flows.get(key)
        if flow is None:
            flow = FlowRecord(
                src_ip=src_ip,
                dst_ip=dst_ip,
                src_port=src_port,
                dst_port=dst_port,
                protocol_name=protocol_name,
                protocol_num=protocol_num,
                start_time=ts,
                last_time=ts,
                fwd_src_ip=src_ip,
                fwd_src_port=src_port,
            )
            self.active_flows[key] = flow

        flow.add_packet(src_ip, src_port, length, ts, tcp_flags)

        # If flow terminated by FIN/RST or reached max active timeout, emit and remove
        if flow.is_closed or (ts - flow.start_time) >= self.active_timeout:
            self._emit_flow(key, flow)

    def _emit_flow(self, key: tuple, flow: FlowRecord):
        """Emits completed flow payload to the subscriber callback."""
        if key in self.active_flows:
            del self.active_flows[key]
        if self.on_flow_complete:
            payload = flow.to_feature_payload()
            try:
                self.on_flow_complete(payload)
            except Exception as e:
                logger.error(f"Error in on_flow_complete callback: {e}")

    def flush_expired_flows(self, current_time: float = None):
        """Scans and flushes flows that have exceeded idle or active timeout."""
        now = current_time if current_time is not None else time.time()
        expired_keys = []

        for key, flow in list(self.active_flows.items()):
            idle_duration = now - flow.last_time
            active_duration = now - flow.start_time

            if idle_duration >= self.idle_timeout or active_duration >= self.active_timeout:
                expired_keys.append(key)

        for key in expired_keys:
            if key in self.active_flows:
                flow = self.active_flows[key]
                self._emit_flow(key, flow)

    def clear(self):
        """Clears all active flows."""
        self.active_flows.clear()
