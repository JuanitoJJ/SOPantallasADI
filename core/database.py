import os
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from core.logger import get_logger


logger = get_logger("core.database")


DB_FILE = "sopantallas_audit.db"
DB_SCHEMA_VERSION = 1


class Database:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._db_lock = threading.RLock()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(DB_FILE, timeout=10, isolation_level=None)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._db_lock:
            try:
                with self._get_conn() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS schema_version (
                            version INTEGER PRIMARY KEY
                        )
                    """)
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS app_launches (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            timestamp TEXT NOT NULL,
                            app_name TEXT NOT NULL,
                            app_path TEXT,
                            action TEXT NOT NULL,
                            pid INTEGER,
                            error TEXT
                        )
                    """)
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS meetings (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            timestamp TEXT NOT NULL,
                            event_id TEXT,
                            subject TEXT NOT NULL,
                            start_time TEXT,
                            end_time TEXT,
                            organizer TEXT,
                            action TEXT NOT NULL,
                            minutes_until INTEGER
                        )
                    """)
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS session_events (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            timestamp TEXT NOT NULL,
                            event_type TEXT NOT NULL,
                            details TEXT
                        )
                    """)
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS notification_events (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            timestamp TEXT NOT NULL,
                            level TEXT NOT NULL,
                            title TEXT NOT NULL,
                            message TEXT
                        )
                    """)
                    cursor.execute(
                        "CREATE INDEX IF NOT EXISTS idx_app_launches_ts ON app_launches(timestamp)"
                    )
                    cursor.execute(
                        "CREATE INDEX IF NOT EXISTS idx_meetings_ts ON meetings(timestamp)"
                    )
                    cursor.execute(
                        "CREATE INDEX IF NOT EXISTS idx_session_ts ON session_events(timestamp)"
                    )
                    cursor.execute(
                        "CREATE INDEX IF NOT EXISTS idx_notif_ts ON notification_events(timestamp)"
                    )

                    cursor.execute("SELECT version FROM schema_version LIMIT 1")
                    row = cursor.fetchone()
                    if row is None:
                        cursor.execute(
                            "INSERT INTO schema_version (version) VALUES (?)",
                            (DB_SCHEMA_VERSION,),
                        )
                        logger.info("Base de datos inicializada (schema v%d)", DB_SCHEMA_VERSION)
                    else:
                        logger.debug("Base de datos ya existe (schema v%s)", row["version"])
            except Exception as exc:
                logger.error("Error inicializando DB: %s", exc, exc_info=True)

    def _now_iso(self) -> str:
        return datetime.now().isoformat(timespec="seconds")

    # ── App launches ────────────────────────────────────────────────
    def log_app_launch(self, app_name: str, app_path: str = "",
                       action: str = "launch", pid: int = None,
                       error: str = None) -> int:
        with self._db_lock:
            try:
                with self._get_conn() as conn:
                    cursor = conn.execute(
                        """INSERT INTO app_launches
                           (timestamp, app_name, app_path, action, pid, error)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (self._now_iso(), app_name, app_path, action, pid, error),
                    )
                    return cursor.lastrowid
            except Exception as exc:
                logger.warning("Error logging app launch: %s", exc)
                return -1

    def get_app_launches(self, since: Optional[datetime] = None,
                         limit: int = 500) -> List[Dict]:
        with self._db_lock:
            try:
                with self._get_conn() as conn:
                    if since:
                        rows = conn.execute(
                            """SELECT * FROM app_launches
                               WHERE timestamp >= ?
                               ORDER BY timestamp DESC LIMIT ?""",
                            (since.isoformat(timespec="seconds"), limit),
                        ).fetchall()
                    else:
                        rows = conn.execute(
                            """SELECT * FROM app_launches
                               ORDER BY timestamp DESC LIMIT ?""",
                            (limit,),
                        ).fetchall()
                    return [dict(r) for r in rows]
            except Exception as exc:
                logger.warning("Error leyendo app_launches: %s", exc)
                return []

    # ── Meetings ────────────────────────────────────────────────────
    def log_meeting_event(self, event_id: str, subject: str,
                          action: str, start_time: str = None,
                          end_time: str = None, organizer: str = None,
                          minutes_until: int = None) -> int:
        with self._db_lock:
            try:
                with self._get_conn() as conn:
                    cursor = conn.execute(
                        """INSERT INTO meetings
                           (timestamp, event_id, subject, start_time, end_time,
                            organizer, action, minutes_until)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (self._now_iso(), event_id, subject, start_time,
                         end_time, organizer, action, minutes_until),
                    )
                    return cursor.lastrowid
            except Exception as exc:
                logger.warning("Error logging meeting: %s", exc)
                return -1

    def get_meeting_events(self, since: Optional[datetime] = None,
                           limit: int = 500) -> List[Dict]:
        with self._db_lock:
            try:
                with self._get_conn() as conn:
                    if since:
                        rows = conn.execute(
                            """SELECT * FROM meetings
                               WHERE timestamp >= ?
                               ORDER BY timestamp DESC LIMIT ?""",
                            (since.isoformat(timespec="seconds"), limit),
                        ).fetchall()
                    else:
                        rows = conn.execute(
                            """SELECT * FROM meetings
                               ORDER BY timestamp DESC LIMIT ?""",
                            (limit,),
                        ).fetchall()
                    return [dict(r) for r in rows]
            except Exception as exc:
                logger.warning("Error leyendo meetings: %s", exc)
                return []

    # ── Session events ──────────────────────────────────────────────
    def log_session(self, event_type: str, details: str = "") -> int:
        with self._db_lock:
            try:
                with self._get_conn() as conn:
                    cursor = conn.execute(
                        """INSERT INTO session_events
                           (timestamp, event_type, details)
                           VALUES (?, ?, ?)""",
                        (self._now_iso(), event_type, details),
                    )
                    return cursor.lastrowid
            except Exception as exc:
                logger.warning("Error logging session: %s", exc)
                return -1

    def get_session_events(self, since: Optional[datetime] = None,
                           limit: int = 200) -> List[Dict]:
        with self._db_lock:
            try:
                with self._get_conn() as conn:
                    if since:
                        rows = conn.execute(
                            """SELECT * FROM session_events
                               WHERE timestamp >= ?
                               ORDER BY timestamp DESC LIMIT ?""",
                            (since.isoformat(timespec="seconds"), limit),
                        ).fetchall()
                    else:
                        rows = conn.execute(
                            """SELECT * FROM session_events
                               ORDER BY timestamp DESC LIMIT ?""",
                            (limit,),
                        ).fetchall()
                    return [dict(r) for r in rows]
            except Exception as exc:
                logger.warning("Error leyendo session_events: %s", exc)
                return []

    # ── Notification events ─────────────────────────────────────────
    def log_notification(self, level: str, title: str, message: str = "") -> int:
        with self._db_lock:
            try:
                with self._get_conn() as conn:
                    cursor = conn.execute(
                        """INSERT INTO notification_events
                           (timestamp, level, title, message)
                           VALUES (?, ?, ?, ?)""",
                        (self._now_iso(), level, title, message),
                    )
                    return cursor.lastrowid
            except Exception as exc:
                logger.warning("Error logging notification: %s", exc)
                return -1

    def get_notification_events(self, since: Optional[datetime] = None,
                                limit: int = 200) -> List[Dict]:
        with self._db_lock:
            try:
                with self._get_conn() as conn:
                    if since:
                        rows = conn.execute(
                            """SELECT * FROM notification_events
                               WHERE timestamp >= ?
                               ORDER BY timestamp DESC LIMIT ?""",
                            (since.isoformat(timespec="seconds"), limit),
                        ).fetchall()
                    else:
                        rows = conn.execute(
                            """SELECT * FROM notification_events
                               ORDER BY timestamp DESC LIMIT ?""",
                            (limit,),
                        ).fetchall()
                    return [dict(r) for r in rows]
            except Exception as exc:
                logger.warning("Error leyendo notification_events: %s", exc)
                return []

    # ── Aggregations / Dashboard ────────────────────────────────────
    def get_app_usage_stats(self, since: Optional[datetime] = None) -> List[Dict]:
        with self._db_lock:
            try:
                with self._get_conn() as conn:
                    if since:
                        rows = conn.execute(
                            """SELECT app_name,
                                      COUNT(*) as total_launches,
                                      SUM(CASE WHEN action='launch' THEN 1 ELSE 0 END) as successful,
                                      SUM(CASE WHEN error IS NOT NULL THEN 1 ELSE 0 END) as errors
                               FROM app_launches
                               WHERE timestamp >= ? AND action IN ('launch','close','error')
                               GROUP BY app_name
                               ORDER BY total_launches DESC""",
                            (since.isoformat(timespec="seconds"),),
                        ).fetchall()
                    else:
                        rows = conn.execute(
                            """SELECT app_name,
                                      COUNT(*) as total_launches,
                                      SUM(CASE WHEN action='launch' THEN 1 ELSE 0 END) as successful,
                                      SUM(CASE WHEN error IS NOT NULL THEN 1 ELSE 0 END) as errors
                               FROM app_launches
                               WHERE action IN ('launch','close','error')
                               GROUP BY app_name
                               ORDER BY total_launches DESC""",
                        ).fetchall()
                    return [dict(r) for r in rows]
            except Exception as exc:
                logger.warning("Error en get_app_usage_stats: %s", exc)
                return []

    def get_meeting_stats(self, since: Optional[datetime] = None) -> Dict:
        with self._db_lock:
            try:
                with self._get_conn() as conn:
                    if since:
                        total = conn.execute(
                            "SELECT COUNT(*) as c FROM meetings WHERE timestamp >= ?",
                            (since.isoformat(timespec="seconds"),),
                        ).fetchone()["c"]
                        alerts = conn.execute(
                            """SELECT COUNT(*) as c FROM meetings
                               WHERE timestamp >= ? AND action='alert'""",
                            (since.isoformat(timespec="seconds"),),
                        ).fetchone()["c"]
                        joined = conn.execute(
                            """SELECT COUNT(*) as c FROM meetings
                               WHERE timestamp >= ? AND action='join'""",
                            (since.isoformat(timespec="seconds"),),
                        ).fetchone()["c"]
                    else:
                        total = conn.execute(
                            "SELECT COUNT(*) as c FROM meetings"
                        ).fetchone()["c"]
                        alerts = conn.execute(
                            "SELECT COUNT(*) as c FROM meetings WHERE action='alert'"
                        ).fetchone()["c"]
                        joined = conn.execute(
                            "SELECT COUNT(*) as c FROM meetings WHERE action='join'"
                        ).fetchone()["c"]
                    return {
                        "total": total,
                        "alerts": alerts,
                        "joined": joined,
                    }
            except Exception as exc:
                logger.warning("Error en get_meeting_stats: %s", exc)
                return {"total": 0, "alerts": 0, "joined": 0}

    def get_overall_stats(self, since: Optional[datetime] = None) -> Dict:
        with self._db_lock:
            try:
                with self._get_conn() as conn:
                    if since:
                        iso = since.isoformat(timespec="seconds")
                        app_total = conn.execute(
                            "SELECT COUNT(*) as c FROM app_launches WHERE timestamp >= ?",
                            (iso,),
                        ).fetchone()["c"]
                        meet_total = conn.execute(
                            "SELECT COUNT(*) as c FROM meetings WHERE timestamp >= ?",
                            (iso,),
                        ).fetchone()["c"]
                        notif_total = conn.execute(
                            "SELECT COUNT(*) as c FROM notification_events WHERE timestamp >= ?",
                            (iso,),
                        ).fetchone()["c"]
                        session_total = conn.execute(
                            "SELECT COUNT(*) as c FROM session_events WHERE timestamp >= ?",
                            (iso,),
                        ).fetchone()["c"]
                    else:
                        app_total = conn.execute("SELECT COUNT(*) as c FROM app_launches").fetchone()["c"]
                        meet_total = conn.execute("SELECT COUNT(*) as c FROM meetings").fetchone()["c"]
                        notif_total = conn.execute("SELECT COUNT(*) as c FROM notification_events").fetchone()["c"]
                        session_total = conn.execute("SELECT COUNT(*) as c FROM session_events").fetchone()["c"]
                    return {
                        "app_launches": app_total,
                        "meetings": meet_total,
                        "notifications": notif_total,
                        "session_events": session_total,
                    }
            except Exception as exc:
                logger.warning("Error en get_overall_stats: %s", exc)
                return {"app_launches": 0, "meetings": 0, "notifications": 0, "session_events": 0}

    def cleanup_old_data(self, days: int = 90) -> int:
        """Elimina registros más antiguos de N días. Retorna filas eliminadas."""
        with self._db_lock:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")
            total_deleted = 0
            for table in ("app_launches", "meetings", "session_events", "notification_events"):
                try:
                    with self._get_conn() as conn:
                        cursor = conn.execute(
                            f"DELETE FROM {table} WHERE timestamp < ?",
                            (cutoff,),
                        )
                        total_deleted += cursor.rowcount
                except Exception as exc:
                    logger.warning("Error limpiando %s: %s", table, exc)
            logger.info("Limpieza DB: %d filas eliminadas (cutoff %s)", total_deleted, cutoff)
            return total_deleted


database = Database()
