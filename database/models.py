"""
SentinelNet AI - Database Models
SQLAlchemy ORM models for intrusion detections and system metrics.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def utc_now():
    return datetime.now(timezone.utc)


class Detection(Base):
    """
    Stores individual flow-level intrusion detections and classification outputs.
    """
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)
    source_ip = Column(String(45), nullable=False, index=True)
    destination_ip = Column(String(45), nullable=False, index=True)
    source_port = Column(Integer, nullable=False)
    destination_port = Column(Integer, nullable=False, index=True)
    protocol = Column(String(10), nullable=False)  # TCP, UDP, ICMP, OTHER
    
    prediction = Column(String(50), nullable=False, index=True)  # NORMAL or specific ATTACK class
    attack_type = Column(String(50), nullable=False)             # BENIGN, DoS, PortScan, BruteForce, etc.
    is_attack = Column(Boolean, default=False, nullable=False, index=True)
    confidence = Column(Float, nullable=False)                    # 0.0 - 1.0 (e.g. 0.985)
    risk_level = Column(String(20), nullable=False, index=True)  # NORMAL, LOW, MEDIUM, HIGH, CRITICAL

    flow_duration = Column(Float, default=0.0)                   # Seconds
    packet_count = Column(Integer, default=0)
    byte_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    def to_dict(self):
        """Convert detection record to JSON-serializable dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "source_ip": self.source_ip,
            "destination_ip": self.destination_ip,
            "source_port": self.source_port,
            "destination_port": self.destination_port,
            "protocol": self.protocol,
            "prediction": self.prediction,
            "attack_type": self.attack_type,
            "is_attack": self.is_attack,
            "confidence": round(float(self.confidence), 4),
            "risk_level": self.risk_level,
            "flow_duration": round(float(self.flow_duration), 4),
            "packet_count": self.packet_count,
            "byte_count": self.byte_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SystemMetric(Base):
    """
    Periodic system and traffic throughput snapshots.
    """
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)
    packets_captured = Column(Integer, default=0)
    flows_processed = Column(Integer, default=0)
    normal_count = Column(Integer, default=0)
    attack_count = Column(Integer, default=0)
    cpu_usage = Column(Float, default=0.0)
    memory_usage = Column(Float, default=0.0)

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "packets_captured": self.packets_captured,
            "flows_processed": self.flows_processed,
            "normal_count": self.normal_count,
            "attack_count": self.attack_count,
            "cpu_usage": round(float(self.cpu_usage), 2),
            "memory_usage": round(float(self.memory_usage), 2),
        }


class MonitoringSession(Base):
    """
    Logs start/stop lifecycle of network monitoring sessions.
    """
    __tablename__ = "monitoring_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    started_at = Column(DateTime, default=utc_now, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    interface_name = Column(String(50), nullable=False)
    packets_captured = Column(Integer, default=0)
    flows_processed = Column(Integer, default=0)
    attacks_detected = Column(Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "interface_name": self.interface_name,
            "packets_captured": self.packets_captured,
            "flows_processed": self.flows_processed,
            "attacks_detected": self.attacks_detected,
        }
