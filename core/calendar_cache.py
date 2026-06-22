import json
import os
from datetime import datetime, timedelta
from core.logger import get_logger


logger = get_logger("core.calendar_cache")


CACHE_DIR = "cache"
CACHE_FILE = "meetings_cache.json"
CACHE_MAX_AGE_HOURS = 6


class MeetingsCache:
    def __init__(self):
        self._cache_dir = CACHE_DIR
        self._cache_file = os.path.join(self._cache_dir, CACHE_FILE)
        self._ensure_dir()

    def _ensure_dir(self):
        if not os.path.exists(self._cache_dir):
            os.makedirs(self._cache_dir, exist_ok=True)

    def save(self, meetings: list):
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "meetings": meetings,
            }
            with open(self._cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug("Cache de reuniones guardado (%d items)", len(meetings))
        except Exception as exc:
            logger.warning("No se pudo guardar cache de reuniones: %s", exc)

    def load(self) -> tuple:
        try:
            if not os.path.exists(self._cache_file):
                return [], False
            with open(self._cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            timestamp = datetime.fromisoformat(data.get("timestamp", "2000-01-01T00:00:00"))
            age = datetime.now() - timestamp
            meetings = data.get("meetings", [])
            if age > timedelta(hours=CACHE_MAX_AGE_HOURS):
                logger.info("Cache expirado (%.1f horas)", age.total_seconds() / 3600)
                return meetings, True
            logger.debug("Cache válido cargado (%d items, %.1f min)", len(meetings), age.total_seconds() / 60)
            return meetings, True
        except Exception as exc:
            logger.warning("No se pudo cargar cache de reuniones: %s", exc)
            return [], False

    def clear(self):
        try:
            if os.path.exists(self._cache_file):
                os.remove(self._cache_file)
                logger.info("Cache de reuniones eliminado")
        except Exception as exc:
            logger.warning("No se pudo eliminar cache: %s", exc)

    def is_fresh(self) -> bool:
        try:
            if not os.path.exists(self._cache_file):
                return False
            with open(self._cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            timestamp = datetime.fromisoformat(data.get("timestamp", "2000-01-01T00:00:00"))
            return (datetime.now() - timestamp) < timedelta(hours=CACHE_MAX_AGE_HOURS)
        except Exception:
            return False
