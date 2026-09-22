"""
SentinelNet AI - Database Session and Engine Manager
Manages MariaDB/MySQL connections with automatic failover to SQLite.
"""

import os
import logging
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from database.models import Base

logger = logging.getLogger("sentinelnet.database")

_engine = None
_SessionFactory = None
_active_db_type = "UNKNOWN"


def get_db_url() -> tuple[str, str]:
    """
    Construct database URL based on environment variables.
    Returns (db_url, db_type).
    """
    use_sqlite_fallback = os.getenv("USE_SQLITE_FALLBACK", "True").lower() in ("true", "1", "yes")
    sqlite_path = os.getenv("SQLITE_DB_PATH", "sqlite:///./sentinelnet.db")

    db_user = os.getenv("DB_USER", "sentinel")
    db_pass = os.getenv("DB_PASSWORD", "sentinel_secure_pass")
    db_host = os.getenv("DB_HOST", "127.0.0.1")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME", "sentinelnet_db")

    mariadb_url = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"

    return mariadb_url, sqlite_path, use_sqlite_fallback


def init_db():
    """
    Initializes the database engine and tables.
    Attempts MariaDB first; gracefully falls back to SQLite.
    """
    global _engine, _SessionFactory, _active_db_type
    
    mariadb_url, sqlite_path, use_sqlite_fallback = get_db_url()

    # Try MariaDB/MySQL first if configured
    try:
        logger.info(f"Attempting connection to MariaDB database...")
        temp_engine = create_engine(
            mariadb_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args={"connect_timeout": 3}
        )
        with temp_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        _engine = temp_engine
        _active_db_type = "MariaDB / MySQL"
        logger.info("Successfully connected to MariaDB / MySQL database.")
    except Exception as e:
        logger.warning(f"MariaDB connection failed ({e}). Checking fallback configuration...")
        if use_sqlite_fallback:
            logger.info(f"Falling back to local SQLite database at: {sqlite_path}")
            _engine = create_engine(
                sqlite_path,
                connect_args={"check_same_thread": False},
                pool_pre_ping=True
            )
            _active_db_type = "SQLite (Local Fallback)"
        else:
            raise RuntimeError(f"Database connection failed and SQLite fallback is disabled: {e}")

    # Create tables
    Base.metadata.create_all(bind=_engine)
    _SessionFactory = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=_engine))
    logger.info(f"Database schema initialized successfully. Active Backend: {_active_db_type}")
    return _engine


def get_engine():
    global _engine
    if _engine is None:
        init_db()
    return _engine


def get_db_session():
    """FastAPI dependency for database sessions."""
    global _SessionFactory
    if _SessionFactory is None:
        init_db()
    session = _SessionFactory()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def session_scope():
    """Transactional scope context manager for background workers."""
    global _SessionFactory
    if _SessionFactory is None:
        init_db()
    session = _SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_database_status() -> dict:
    """Returns the current database connection status."""
    global _engine, _active_db_type
    if _engine is None:
        try:
            init_db()
        except Exception as e:
            return {"status": "DISCONNECTED", "type": "NONE", "error": str(e)}

    try:
        with _engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "CONNECTED", "type": _active_db_type, "error": None}
    except Exception as e:
        return {"status": "ERROR", "type": _active_db_type, "error": str(e)}
