import os
import json
from datetime import datetime
from core.logger import get_logger


logger = get_logger("core.notification_manager")


NOTIFICATION_HISTORY_FILE = "notification_history.json"
MAX_HISTORY_ITEMS = 50


class NotificationLevel:
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    MEETING = "meeting"


class Notification:
    def __init__(self, level: str, title: str, message: str = "",
                 action_callback=None, action_label: str = ""):
        self.id = id(self)
        self.level = level
        self.title = title
        self.message = message
        self.timestamp = datetime.now()
        self.read = False
        self.action_callback = action_callback
        self.action_label = action_label

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "level": self.level,
            "title": self.title,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "read": self.read,
        }

    def time_str(self) -> str:
        return self.timestamp.strftime("%H:%M")


class NotificationManager:
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
        self._history: list = []
        self._listeners = []
        self._load_history()

    def add_listener(self, callback):
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def notify(self, level: str, title: str, message: str = "",
               action_callback=None, action_label: str = "",
               play_sound: bool = True) -> Notification:
        notif = Notification(
            level=level,
            title=title,
            message=message,
            action_callback=action_callback,
            action_label=action_label,
        )
        self._history.insert(0, notif)
        if len(self._history) > MAX_HISTORY_ITEMS:
            self._history = self._history[:MAX_HISTORY_ITEMS]
        self._save_history()
        logger.info("Notificación [%s]: %s — %s", level, title, message)
        self._fire_listeners(notif)
        if play_sound:
            self._maybe_play_sound(level)
        return notif

    def get_history(self) -> list:
        return list(self._history)

    def get_unread_count(self) -> int:
        return sum(1 for n in self._history if not n.read)

    def mark_all_read(self):
        for n in self._history:
            n.read = True
        self._save_history()
        self._fire_listeners(None)

    def clear(self):
        self._history.clear()
        self._save_history()
        self._fire_listeners(None)

    def _fire_listeners(self, notification):
        for cb in list(self._listeners):
            try:
                cb(notification)
            except Exception as exc:
                logger.warning("Listener de notificación falló: %s", exc)

    def _maybe_play_sound(self, level: str):
        try:
            from core.sound_player import play_notification_sound
            play_notification_sound(level)
        except Exception as exc:
            logger.debug("No se pudo reproducir sonido: %s", exc)

    def _save_history(self):
        try:
            data = [n.to_dict() for n in self._history]
            with open(NOTIFICATION_HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            logger.warning("No se pudo guardar historial: %s", exc)

    def _load_history(self):
        if not os.path.exists(NOTIFICATION_HISTORY_FILE):
            return
        try:
            with open(NOTIFICATION_HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._history = []
            for item in data:
                notif = Notification(
                    level=item.get("level", NotificationLevel.INFO),
                    title=item.get("title", ""),
                    message=item.get("message", ""),
                )
                notif.id = item.get("id", id(notif))
                notif.read = item.get("read", False)
                try:
                    notif.timestamp = datetime.fromisoformat(item["timestamp"])
                except Exception:
                    notif.timestamp = datetime.now()
                self._history.append(notif)
            logger.info("Cargadas %d notificaciones del historial", len(self._history))
        except Exception as exc:
            logger.warning("No se pudo cargar historial: %s", exc)


notification_manager = NotificationManager()
