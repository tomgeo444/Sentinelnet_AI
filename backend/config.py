"""
SentinelNet AI - Configuration Management
Loads system settings from environment variables and .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings:
    # Server
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    # Database
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "sentinel")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "sentinel_secure_pass")
    DB_NAME: str = os.getenv("DB_NAME", "sentinelnet_db")
    USE_SQLITE_FALLBACK: bool = os.getenv("USE_SQLITE_FALLBACK", "True").lower() in ("true", "1", "yes")
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "sqlite:///./sentinelnet.db")

    # Network Capture
    NETWORK_INTERFACE: str = os.getenv("NETWORK_INTERFACE", "")
    SERVER_PORT_FILTER: int = int(os.getenv("SERVER_PORT_FILTER", "8000"))
    FLOW_IDLE_TIMEOUT: float = float(os.getenv("FLOW_IDLE_TIMEOUT", "2.0"))
    FLOW_ACTIVE_TIMEOUT: float = float(os.getenv("FLOW_ACTIVE_TIMEOUT", "10.0"))

    # ML Model Artifacts
    MODEL_PATH: str = os.getenv("MODEL_PATH", "models/sentinelnet_model.pt")
    SCALER_PATH: str = os.getenv("SCALER_PATH", "models/scaler.joblib")
    LABEL_ENCODER_PATH: str = os.getenv("LABEL_ENCODER_PATH", "models/label_encoder.joblib")
    FEATURE_NAMES_PATH: str = os.getenv("FEATURE_NAMES_PATH", "models/feature_names.json")
    METRICS_PATH: str = os.getenv("METRICS_PATH", "models/model_metrics.json")

    # Risk Engine
    RISK_THRESHOLD_LOW: float = float(os.getenv("RISK_THRESHOLD_LOW", "0.40"))
    RISK_THRESHOLD_MEDIUM: float = float(os.getenv("RISK_THRESHOLD_MEDIUM", "0.65"))
    RISK_THRESHOLD_HIGH: float = float(os.getenv("RISK_THRESHOLD_HIGH", "0.85"))
    RISK_THRESHOLD_CRITICAL: float = float(os.getenv("RISK_THRESHOLD_CRITICAL", "0.95"))


settings = Settings()
