"""
SentinelNet AI - Central Monitoring Orchestrator Service
Integrates live packet capture, bidirectional flow aggregation, deep learning inference,
database logging, and real-time WebSocket broadcasting.
"""

import time
import asyncio
import logging
import threading
from datetime import datetime, timezone
from collections import deque, defaultdict
import psutil

from backend.config import settings
from backend.websocket.manager import ws_manager
from backend.services.risk_engine import RiskEngine
from capture.flow_manager import FlowManager
from capture.packet_capture import LivePacketCapture, get_default_interface
from ml.predictor import SentinelNetPredictor
from database.database import session_scope
from database.models import Detection, SystemMetric, MonitoringSession

logger = logging.getLogger("sentinelnet.monitor")


class MonitorService:
    """
    Singleton service governing the entire live detection and streaming lifecycle.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.predictor = SentinelNetPredictor(
            model_path=settings.MODEL_PATH,
            scaler_path=settings.SCALER_PATH,
            encoder_path=settings.LABEL_ENCODER_PATH,
            features_path=settings.FEATURE_NAMES_PATH,
            metrics_path=settings.METRICS_PATH,
        )

        self.flow_manager = FlowManager(
            idle_timeout=settings.FLOW_IDLE_TIMEOUT,
            active_timeout=settings.FLOW_ACTIVE_TIMEOUT,
            on_flow_complete=self._on_flow_completed,
        )

        self.capture: LivePacketCapture = None
        self.is_monitoring = False
        self.active_interface = settings.NETWORK_INTERFACE or get_default_interface()
        self.session_start_time = None

        # Live Real-time Statistics
        self.stats = {
            "packets_captured": 0,
            "flows_processed": 0,
            "normal_count": 0,
            "suspicious_count": 0,
            "attack_count": 0,
            "bytes_captured": 0,
            "attack_distribution": defaultdict(int),
            "protocol_distribution": defaultdict(int),
        }

        # Sliding window history for charts
        self.recent_detections = deque(maxlen=100)
        self.traffic_history = deque(maxlen=30)  # Last 30 time steps
        self.latest_alert = None

        self._stats_task = None
        self._loop = None
        self._lock = threading.Lock()
        self._initialized = True

    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        """Sets the active asyncio event loop for threadsafe WebSocket dispatches."""
        self._loop = loop

    def start_monitoring(self, interface: str = None) -> dict:
        """Starts live packet capture and continuous intrusion inference."""
        with self._lock:
            if self.is_monitoring:
                return {"status": "ALREADY_RUNNING", "interface": self.active_interface}

            iface = interface or self.active_interface or get_default_interface()
            self.active_interface = iface

            self.capture = LivePacketCapture(
                interface=self.active_interface,
                server_port_filter=settings.SERVER_PORT_FILTER,
                flow_manager=self.flow_manager,
                on_packet_callback=self._on_packet_captured,
            )

            self.session_start_time = time.time()
            self.is_monitoring = True
            self.capture.start()

            logger.info(f"Live monitoring started on interface: {self.active_interface}")

            # Notify WebSockets
            if self._loop and self._loop.is_running():
                ws_manager.broadcast_sync({
                    "type": "MONITORING_STATUS_CHANGE",
                    "data": self.get_status(),
                }, self._loop)

            return {"status": "STARTED", "interface": self.active_interface}

    def stop_monitoring(self) -> dict:
        """Stops packet capture cleanly and finalizes telemetry."""
        with self._lock:
            if not self.is_monitoring:
                return {"status": "NOT_RUNNING", "interface": self.active_interface}

            self.is_monitoring = False
            if self.capture:
                self.capture.stop()
                self.capture = None

            logger.info("Live monitoring stopped.")

            # Notify WebSockets
            if self._loop and self._loop.is_running():
                ws_manager.broadcast_sync({
                    "type": "MONITORING_STATUS_CHANGE",
                    "data": self.get_status(),
                }, self._loop)

            return {"status": "STOPPED", "interface": self.active_interface}

    def _on_packet_captured(self, pkt_info: dict):
        """Callback executed on every captured packet."""
        with self._lock:
            self.stats["packets_captured"] += 1
            self.stats["bytes_captured"] += pkt_info.get("length", 0)
            proto = pkt_info.get("protocol", "OTHER")
            self.stats["protocol_distribution"][proto] += 1

    def _on_flow_completed(self, flow_payload: dict):
        """
        Processes a finished network flow:
        1. Executes Deep Learning inference
        2. Computes risk severity
        3. Persists detection in database
        4. Broadcasts live event and alerts via WebSocket
        """
        features = flow_payload["features"]
        prediction_result = self.predictor.predict_flow(features)

        pred_class = prediction_result["prediction"]
        is_attack = prediction_result["is_attack"]
        confidence = prediction_result["confidence"]
        risk_level = RiskEngine.evaluate_risk(pred_class, confidence, is_attack)

        # Build Detection Object
        detection_data = {
            "source_ip": flow_payload["source_ip"],
            "destination_ip": flow_payload["destination_ip"],
            "source_port": flow_payload["source_port"],
            "destination_port": flow_payload["destination_port"],
            "protocol": flow_payload["protocol"],
            "prediction": pred_class,
            "attack_type": pred_class,
            "is_attack": is_attack,
            "confidence": confidence,
            "risk_level": risk_level,
            "flow_duration": flow_payload["duration"],
            "packet_count": flow_payload["packet_count"],
            "byte_count": flow_payload["byte_count"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Update in-memory statistics
        with self._lock:
            self.stats["flows_processed"] += 1
            if is_attack:
                self.stats["attack_count"] += 1
                self.stats["attack_distribution"][pred_class] += 1
                if risk_level in ("HIGH", "CRITICAL"):
                    self.stats["suspicious_count"] += 1
                self.latest_alert = detection_data
            else:
                self.stats["normal_count"] += 1

            self.recent_detections.appendleft(detection_data)

        # Asynchronously store to Database
        try:
            with session_scope() as session:
                record = Detection(
                    source_ip=detection_data["source_ip"],
                    destination_ip=detection_data["destination_ip"],
                    source_port=detection_data["source_port"],
                    destination_port=detection_data["destination_port"],
                    protocol=detection_data["protocol"],
                    prediction=detection_data["prediction"],
                    attack_type=detection_data["attack_type"],
                    is_attack=detection_data["is_attack"],
                    confidence=detection_data["confidence"],
                    risk_level=detection_data["risk_level"],
                    flow_duration=detection_data["flow_duration"],
                    packet_count=detection_data["packet_count"],
                    byte_count=detection_data["byte_count"],
                )
                session.add(record)
        except Exception as e:
            logger.error(f"Error persisting detection to database: {e}")

        # Broadcast WebSocket events
        if self._loop and self._loop.is_running():
            # 1. New Detection Event
            ws_manager.broadcast_sync({
                "type": "NEW_DETECTION",
                "data": detection_data,
            }, self._loop)

            # 2. High-priority Alert Event if Attack
            if is_attack:
                ws_manager.broadcast_sync({
                    "type": "ALERT",
                    "data": detection_data,
                }, self._loop)

            # 3. Stream updated stats
            ws_manager.broadcast_sync({
                "type": "STATS_UPDATE",
                "data": self.get_statistics(),
            }, self._loop)

    def get_status(self) -> dict:
        """Returns overall system health and monitoring state."""
        return {
            "monitoring_active": self.is_monitoring,
            "active_interface": self.active_interface,
            "model_loaded": self.predictor.is_loaded,
            "session_uptime_seconds": round(time.time() - self.session_start_time, 1) if (self.is_monitoring and self.session_start_time) else 0,
        }

    def get_statistics(self) -> dict:
        """Returns aggregated telemetry and flow statistics."""
        with self._lock:
            return {
                "packets_captured": self.stats["packets_captured"],
                "flows_processed": self.stats["flows_processed"],
                "normal_count": self.stats["normal_count"],
                "suspicious_count": self.stats["suspicious_count"],
                "attack_count": self.stats["attack_count"],
                "bytes_captured": self.stats["bytes_captured"],
                "attack_distribution": dict(self.stats["attack_distribution"]),
                "protocol_distribution": dict(self.stats["protocol_distribution"]),
                "latest_alert": self.latest_alert,
                "system_metrics": {
                    "cpu_percent": psutil.cpu_percent(interval=None),
                    "memory_percent": psutil.virtual_memory().percent,
                }
            }

    def get_recent_detections(self, limit: int = 50) -> list[dict]:
        """Returns the most recent detection events."""
        with self._lock:
            return list(self.recent_detections)[:limit]


monitor_service = MonitorService()
