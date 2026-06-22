import os
import json
from datetime import datetime, date
from core.logger import get_logger
from core.path_utils import get_resource_path


logger = get_logger("ui.screensaver.events")


DEFAULT_EVENTS = [
    {
        "date": "01-01",
        "title": "Feliz Año Nuevo",
        "message": "Comienza un nuevo año lleno de oportunidades.",
    },
    {
        "date": "05-01",
        "title": "Día del Trabajo",
        "message": "Celebramos el esfuerzo de cada persona del equipo.",
    },
    {
        "date": "12-25",
        "title": "Feliz Navidad",
        "message": "Paz, salud y éxitos para ti y tu familia.",
    },
    {
        "date": "10-12",
        "title": "Día de la Hispanidad",
        "message": "Celebramos nuestra cultura y unidad.",
    },
]


class EventsManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._events = list(DEFAULT_EVENTS)
        self._load_custom()

    def _load_custom(self):
        path = get_resource_path(os.path.join("assets", "events.json"))
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                self._events.extend(data)
                logger.info("Cargados %d eventos personalizados", len(data))
        except Exception as exc:
            logger.warning("Error cargando eventos: %s", exc)

    def get_today_event(self) -> dict:
        """Retorna evento del día si existe, si no None."""
        today = date.today()
        today_str = today.strftime("%m-%d")
        for event in self._events:
            if event.get("date") == today_str:
                return event
        return None

    def get_upcoming_event(self, within_days: int = 7) -> dict:
        """Retorna próximo evento en los siguientes N días."""
        today = date.today()
        for offset in range(within_days + 1):
            check = date.fromordinal(today.toordinal() + offset)
            check_str = check.strftime("%m-%d")
            for event in self._events:
                if event.get("date") == check_str:
                    days_until = (check - today).days
                    result = dict(event)
                    result["days_until"] = days_until
                    return result
        return None

    def get_count(self) -> int:
        return len(self._events)


events_manager = EventsManager()
