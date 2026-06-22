"""
audit.py — Capa de auditoría sobre la base de datos SQLite.

Provee funciones de alto nivel para registrar eventos de uso:
- Lanzamientos y cierres de aplicaciones
- Reuniones: alertas, joins, finalizaciones
- Sesiones: arranque, fin, screensaver
- Notificaciones
"""
import os
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from core.database import database
from core.logger import get_logger


logger = get_logger("core.audit")


# ── App launches ─────────────────────────────────────────────────
def log_app_launched(app_name: str, app_path: str = "", pid: int = None):
    database.log_app_launch(app_name, app_path, "launch", pid=pid)


def log_app_closed(app_name: str, app_path: str = "", pid: int = None):
    database.log_app_launch(app_name, app_path, "close", pid=pid)


def log_app_launch_failed(app_name: str, app_path: str = "", error: str = ""):
    database.log_app_launch(app_name, app_path, "error", error=error)


# ── Meetings ─────────────────────────────────────────────────────
def log_meeting_alert(event_id: str, subject: str, start_time: str = None,
                      minutes_until: int = None):
    database.log_meeting_event(
        event_id, subject, "alert",
        start_time=start_time,
        minutes_until=minutes_until,
    )


def log_meeting_started(event_id: str, subject: str, start_time: str = None):
    database.log_meeting_event(event_id, subject, "start", start_time=start_time)


def log_meeting_joined(event_id: str, subject: str, start_time: str = None):
    database.log_meeting_event(event_id, subject, "join", start_time=start_time)


def log_meeting_ended(event_id: str, subject: str, end_time: str = None):
    database.log_meeting_event(event_id, subject, "end", end_time=end_time)


# ── Session ──────────────────────────────────────────────────────
def log_session_start(details: str = ""):
    database.log_session("start", details)


def log_session_end(details: str = ""):
    database.log_session("end", details)


def log_screensaver_activated():
    database.log_session("screensaver_on")


def log_screensaver_dismissed():
    database.log_session("screensaver_off")


def log_kiosk_exit():
    database.log_session("kiosk_exit")


# ── Notifications ────────────────────────────────────────────────
def log_notification(level: str, title: str, message: str = ""):
    database.log_notification(level, title, message)


# ── Reports / Queries ────────────────────────────────────────────
def get_overall_stats(since: Optional[datetime] = None) -> Dict:
    return database.get_overall_stats(since)


def get_app_usage(since: Optional[datetime] = None) -> List[Dict]:
    return database.get_app_usage_stats(since)


def get_meeting_stats(since: Optional[datetime] = None) -> Dict:
    return database.get_meeting_stats(since)


def get_recent_apps(since: Optional[datetime] = None, limit: int = 200) -> List[Dict]:
    return database.get_app_launches(since, limit)


def get_recent_meetings(since: Optional[datetime] = None, limit: int = 200) -> List[Dict]:
    return database.get_meeting_events(since, limit)


def get_recent_sessions(since: Optional[datetime] = None, limit: int = 200) -> List[Dict]:
    return database.get_session_events(since, limit)


def get_recent_notifications(since: Optional[datetime] = None, limit: int = 200) -> List[Dict]:
    return database.get_notification_events(since, limit)


# ── CSV Export ───────────────────────────────────────────────────
def export_csv(output_path: str, days: int = 30) -> bool:
    """Exporta un reporte CSV con todas las tablas en el rango.

    Retorna True si éxito.
    """
    try:
        since = datetime.now() - timedelta(days=days)
        overall = get_overall_stats(since)
        app_usage = get_app_usage(since)
        meeting_stats = get_meeting_stats(since)
        recent_apps = get_recent_apps(since, limit=1000)
        recent_meetings = get_recent_meetings(since, limit=1000)
        recent_sessions = get_recent_sessions(since, limit=500)
        recent_notifs = get_recent_notifications(since, limit=500)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            writer.writerow(["REPORTE DE USO — SOPantallasADI"])
            writer.writerow([f"Generado:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            writer.writerow([f"Período:", f"Últimos {days} días"])
            writer.writerow([f"Desde:", since.strftime("%Y-%m-%d %H:%M:%S")])
            writer.writerow([])

            writer.writerow(["=== RESUMEN GENERAL ==="])
            writer.writerow(["Métrica", "Cantidad"])
            writer.writerow(["Total eventos de apps", overall.get("app_launches", 0)])
            writer.writerow(["Total eventos de reuniones", overall.get("meetings", 0)])
            writer.writerow(["Total notificaciones", overall.get("notifications", 0)])
            writer.writerow(["Eventos de sesión", overall.get("session_events", 0)])
            writer.writerow([])

            writer.writerow(["=== USO DE APLICACIONES ==="])
            writer.writerow(["Aplicación", "Lanzamientos totales", "Exitosos", "Errores"])
            for row in app_usage:
                writer.writerow([
                    row.get("app_name", ""),
                    row.get("total_launches", 0),
                    row.get("successful", 0) or 0,
                    row.get("errors", 0) or 0,
                ])
            writer.writerow([])

            writer.writerow(["=== ESTADÍSTICAS DE REUNIONES ==="])
            writer.writerow(["Métrica", "Cantidad"])
            writer.writerow(["Total eventos", meeting_stats.get("total", 0)])
            writer.writerow(["Alertas enviadas", meeting_stats.get("alerts", 0)])
            writer.writerow(["Reuniones unidas", meeting_stats.get("joined", 0)])
            writer.writerow([])

            writer.writerow(["=== HISTORIAL DE LANZAMIENTOS ==="])
            writer.writerow(["Timestamp", "App", "Path", "Acción", "PID", "Error"])
            for row in recent_apps:
                writer.writerow([
                    row.get("timestamp", ""),
                    row.get("app_name", ""),
                    row.get("app_path", ""),
                    row.get("action", ""),
                    row.get("pid", ""),
                    row.get("error", ""),
                ])
            writer.writerow([])

            writer.writerow(["=== HISTORIAL DE REUNIONES ==="])
            writer.writerow(["Timestamp", "Subject", "Start", "End", "Acción", "Minutos antes"])
            for row in recent_meetings:
                writer.writerow([
                    row.get("timestamp", ""),
                    row.get("subject", ""),
                    row.get("start_time", ""),
                    row.get("end_time", ""),
                    row.get("action", ""),
                    row.get("minutes_until", ""),
                ])
            writer.writerow([])

            writer.writerow(["=== EVENTOS DE SESIÓN ==="])
            writer.writerow(["Timestamp", "Tipo", "Detalles"])
            for row in recent_sessions:
                writer.writerow([
                    row.get("timestamp", ""),
                    row.get("event_type", ""),
                    row.get("details", ""),
                ])
            writer.writerow([])

            writer.writerow(["=== NOTIFICACIONES ==="])
            writer.writerow(["Timestamp", "Nivel", "Título", "Mensaje"])
            for row in recent_notifs:
                writer.writerow([
                    row.get("timestamp", ""),
                    row.get("level", ""),
                    row.get("title", ""),
                    row.get("message", ""),
                ])

        logger.info("Reporte CSV exportado: %s (%d días)", output_path, days)
        return True
    except Exception as exc:
        logger.error("Error exportando CSV: %s", exc, exc_info=True)
        return False


def cleanup_old_audit(days: int = 90) -> int:
    return database.cleanup_old_data(days)
