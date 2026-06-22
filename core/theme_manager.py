import os
import re
from core.logger import get_logger
from core.path_utils import get_resource_path


logger = get_logger("core.theme_manager")


THEME_DARK = "dark"
THEME_LIGHT = "light"
THEME_HIGH_CONTRAST = "high_contrast"

THEMES = {
    THEME_DARK: {
        "label": "Oscuro",
        "file": "dark.qss",
        "description": "Fondo oscuro (#1a1a1a) con acentos azules",
    },
    THEME_LIGHT: {
        "label": "Claro",
        "file": "light.qss",
        "description": "Fondo claro (#f5f7fa) con acentos azules",
    },
    THEME_HIGH_CONTRAST: {
        "label": "Alto Contraste",
        "file": "high_contrast.qss",
        "description": "Máximo contraste (#000000/#ffff00) para baja visión",
    },
}

DEFAULT_THEME = THEME_DARK


class ThemeManager:
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
        self._current_theme = DEFAULT_THEME
        self._cached_stylesheets = {}
        self._listeners = []

    def get_available_themes(self) -> list:
        """Retorna lista de tuplas (id, label, description) para selector."""
        return [
            (theme_id, data["label"], data["description"])
            for theme_id, data in THEMES.items()
        ]

    def get_current_theme(self) -> str:
        return self._current_theme

    def set_theme(self, theme_id: str):
        if theme_id not in THEMES:
            logger.warning("Tema '%s' no existe, usando default", theme_id)
            theme_id = DEFAULT_THEME
        if theme_id != self._current_theme:
            self._current_theme = theme_id
            logger.info("Tema cambiado a: %s (%s)", theme_id, THEMES[theme_id]["label"])
            self._notify_listeners(theme_id)

    def register_listener(self, callback):
        """Registra callback que se ejecuta cuando cambia el tema.

        El callback recibe el theme_id como argumento.
        """
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unregister_listener(self, callback):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify_listeners(self, theme_id: str):
        for cb in list(self._listeners):
            try:
                cb(theme_id)
            except Exception as exc:
                logger.warning("Listener de tema falló: %s", exc)

    def load_stylesheet(self, theme_id: str = None) -> str:
        """Carga y devuelve el QSS del tema solicitado, con URLs resueltas."""
        if theme_id is None:
            theme_id = self._current_theme
        if theme_id not in THEMES:
            theme_id = DEFAULT_THEME

        if theme_id in self._cached_stylesheets:
            return self._cached_stylesheets[theme_id]

        qss_path = get_resource_path(
            os.path.join("ui", "styles", "themes", THEMES[theme_id]["file"])
        )
        if not os.path.exists(qss_path):
            logger.error("No se encontró el archivo de tema: %s", qss_path)
            return ""

        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                content = f.read()

            content = self._resolve_urls(content)
            self._cached_stylesheets[theme_id] = content
            logger.debug("Tema '%s' cargado (%d chars)", theme_id, len(content))
            return content
        except Exception as exc:
            logger.error("Error cargando tema '%s': %s", theme_id, exc)
            return ""

    def apply_to(self, app, theme_id: str = None) -> bool:
        """Aplica el tema a una instancia de QApplication."""
        qss = self.load_stylesheet(theme_id)
        if not qss:
            return False
        if theme_id:
            self.set_theme(theme_id)
        app.setStyleSheet(qss)
        logger.info("Tema aplicado: %s", self._current_theme)
        return True

    def apply(self, app):
        """Atajo para aplicar el tema actual."""
        return self.apply_to(app, self._current_theme)

    def invalidate_cache(self):
        """Limpia el cache (útil para desarrollo o recarga en caliente)."""
        self._cached_stylesheets.clear()
        logger.debug("Cache de QSS invalidado")

    def _resolve_urls(self, content: str) -> str:
        def resolve_url(match):
            path = match.group(1).strip("'\"")
            if not os.path.isabs(path):
                abs_path = get_resource_path(path).replace("\\", "/")
                return f"url('{abs_path}')"
            return match.group(0)

        return re.sub(r"url\((.*?)\)", resolve_url, content)


theme_manager = ThemeManager()
