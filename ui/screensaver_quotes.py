import os
import json
import random
from datetime import datetime
from core.logger import get_logger
from core.path_utils import get_resource_path


logger = get_logger("ui.screensaver.quotes")


DEFAULT_QUOTES = [
    "La colaboración es el combustible que permite a los equipos alcanzar lo imposible.",
    "Las mejores ideas nacen cuando diferentes mentes se unen con un propósito común.",
    "Una reunión bien preparada vale más que una hora de trabajo improvisado.",
    "El respeto y la escucha activa son la base de toda comunicación efectiva.",
    "Innovar no es solo crear, es transformar ideas en resultados.",
    "Cada reunión es una oportunidad para aprender algo nuevo.",
    "La puntualidad es la primera muestra de respeto hacia los demás.",
    "Los grandes logros siempre empiezan con un equipo comprometido.",
    "El éxito se construye con pequeñas acciones hechas con consistencia.",
    "Una buena comunicación convierte ideas en realidades.",
    "Piensa en grande, actúa en pequeño, mide siempre.",
    "La diversidad de pensamiento es la mayor fortaleza de un equipo.",
]


class QuotesManager:
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
        self._quotes = list(DEFAULT_QUOTES)
        self._load_custom()

    def _load_custom(self):
        """Carga quotes personalizadas desde assets/quotes.json si existe."""
        path = get_resource_path(os.path.join("assets", "quotes.json"))
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                self._quotes.extend([q for q in data if isinstance(q, str) and q.strip()])
                logger.info("Cargadas %d quotes personalizadas", len(data))
        except Exception as exc:
            logger.warning("Error cargando quotes personalizadas: %s", exc)

    def get_random(self) -> str:
        if not self._quotes:
            return "La colaboración hace grandes cosas."
        return random.choice(self._quotes)

    def get_daily(self) -> str:
        """Quote determinística basada en el día (mismo día → misma quote)."""
        if not self._quotes:
            return "La colaboración hace grandes cosas."
        day_of_year = datetime.now().timetuple().tm_yday
        return self._quotes[day_of_year % len(self._quotes)]

    def get_count(self) -> int:
        return len(self._quotes)

    def add_custom(self, quote: str):
        if quote and quote.strip():
            self._quotes.append(quote.strip())


quotes_manager = QuotesManager()
