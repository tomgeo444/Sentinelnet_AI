"""
SentinelNet AI - REST API Router
Exposes system endpoints for health checks, telemetry, model metrics, monitoring controls, and demo triggers.
"""

import threading
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel

from backend.services.monitor_service import monitor_service
from capture.packet_capture import list_network_interfaces
from database.database import get_database_status, session_scope
from database.models import Detection

logger = logging.getLogger("sentinelnet.api")
router = APIRouter(prefix="/api", tags=["SentinelNet API"])


class MonitoringStartRequest(BaseModel):
    interface: Optional[str] = None


class DemoTriggerRequest(BaseModel):
    mode: str = "normal"  # normal, burst, portscan, synflood, connection-test
    count: int = 15


@router.get("/health")
def get_health():
    """System overall health check."""
    db_status = get_database_status()
    mon_status = monitor_service.get_status()
    stats = monitor_service.get_statistics()

    return {
        "status": "ONLINE",
        "database": db_status,
        "monitoring": mon_status,
        "model_loaded": mon_status["model_loaded"],
        "system_metrics": stats["system_metrics"],
    }


@router.get("/interfaces")
def get_interfaces():
    """Enumerates available host network interfaces."""
    return {
        "interfaces": list_network_interfaces(),
        "active_interface": monitor_service.active_interface,
    }


@router.get("/model/info")
def get_model_info():
    """Returns deep learning model metadata and test set evaluation metrics."""
    info = monitor_service.predictor.get_model_info()
    return info


@router.get("/statistics")
def get_statistics():
    """Returns real-time packet, flow, and threat statistics."""
    return monitor_service.get_statistics()


@router.get("/detections/recent")
def get_recent_detections(limit: int = Query(default=50, ge=1, le=200)):
    """Returns the most recent live flow detections."""
    return {
        "detections": monitor_service.get_recent_detections(limit=limit),
        "total_returned": len(monitor_service.get_recent_detections(limit=limit)),
    }


@router.get("/detections")
def get_detections(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    attack_only: bool = Query(default=False),
    risk_level: Optional[str] = None,
):
    """Queries historical detections from MariaDB / SQLite."""
    with session_scope() as session:
        query = session.query(Detection)
        if attack_only:
            query = query.filter(Detection.is_attack == True)
        if risk_level:
            query = query.filter(Detection.risk_level == risk_level.upper())

        total = query.count()
        records = query.order_by(Detection.timestamp.desc()).offset(offset).limit(limit).all()
        results = [r.to_dict() for r in records]

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "detections": results,
    }


@router.post("/monitoring/start")
def start_monitoring(req: MonitoringStartRequest = None):
    """Starts live packet capture and continuous intrusion inference."""
    iface = req.interface if req else None
    result = monitor_service.start_monitoring(interface=iface)
    return result


@router.post("/monitoring/stop")
def stop_monitoring():
    """Stops live packet capture."""
    result = monitor_service.stop_monitoring()
    return result


@router.get("/monitoring/status")
def get_monitoring_status():
    """Returns live monitoring status."""
    return monitor_service.get_status()


@router.post("/demo/trigger")
def trigger_demo_traffic(req: DemoTriggerRequest, background_tasks: BackgroundTasks):
    """Triggers safe demonstration traffic generation against localhost."""
    from demo.demo_traffic import generate_safe_traffic

    def _run_demo():
        try:
            generate_safe_traffic(mode=req.mode, count=req.count)
        except Exception as e:
            logger.error(f"Error running demo traffic: {e}")

    background_tasks.add_task(_run_demo)
    return {
        "status": "QUEUED",
        "mode": req.mode,
        "message": f"Safe local traffic generation started in mode '{req.mode}' ({req.count} events)."
    }
