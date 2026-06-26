import os
import re
from core.logger import get_logger
from core.path_utils import get_resource_path
from core.design_tokens import (
    ThemeTokens,
    THEMES as TOKEN_THEMES,
    DARK,
    LIGHT,
    HIGH_CONTRAST,
    THEME_DARK,
    THEME_LIGHT,
    THEME_HIGH_CONTRAST,
    DEFAULT_THEME,
    get_tokens as _tokens_for,
)


logger = get_logger("core.theme_manager")


THEMES = {
    THEME_DARK: {
        "label": "Oscuro",
        "file": "dark.qss",
        "description": "Slate cálido con acento ámbar — sala nocturna",
        "tokens": DARK,
    },
    THEME_LIGHT: {
        "label": "Claro",
        "file": "light.qss",
        "description": "Warm-paper con acento ámbar profundo — sala diurna",
        "tokens": LIGHT,
    },
    THEME_HIGH_CONTRAST: {
        "label": "Alto Contraste",
        "file": "high_contrast.qss",
        "description": "Negro absoluto con amarillo WCAG AAA — accesibilidad",
        "tokens": HIGH_CONTRAST,
    },
}


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
        self._cached_tokens = {}
        self._listeners = []

    def get_available_themes(self) -> list:
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
            self._cached_stylesheets.pop(theme_id, None)
            logger.info("Tema cambiado a: %s (%s)", theme_id, THEMES[theme_id]["label"])
            self._notify_listeners(theme_id)

    def register_listener(self, callback):
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

    def get_tokens(self, theme_id: str = None) -> ThemeTokens:
        if theme_id is None:
            theme_id = self._current_theme
        if theme_id not in THEMES:
            theme_id = DEFAULT_THEME
        return THEMES[theme_id]["tokens"]

    def current_tokens(self) -> ThemeTokens:
        return self.get_tokens(self._current_theme)

    def load_stylesheet(self, theme_id: str = None) -> str:
        if theme_id is None:
            theme_id = self._current_theme
        if theme_id not in THEMES:
            theme_id = DEFAULT_THEME

        if theme_id in self._cached_stylesheets:
            return self._cached_stylesheets[theme_id]

        try:
            from core.qss_generator import generate_qss
        except Exception as exc:
            logger.error("No se pudo cargar qss_generator: %s", exc)
            return self._load_legacy_stylesheet(theme_id)

        tokens = THEMES[theme_id]["tokens"]
        try:
            content = generate_qss(tokens)
            content = self._resolve_urls(content)
            self._cached_stylesheets[theme_id] = content
            logger.debug("Tema '%s' generado desde tokens (%d chars)", theme_id, len(content))
            return content
        except Exception as exc:
            logger.error("Error generando QSS para '%s': %s", theme_id, exc)
            return self._load_legacy_stylesheet(theme_id)

    def _load_legacy_stylesheet(self, theme_id: str) -> str:
        qss_path = get_resource_path(
            os.path.join("ui", "styles", "themes", THEMES[theme_id]["file"])
        )
        if not os.path.exists(qss_path):
            logger.error("No se encontró el archivo de tema legacy: %s", qss_path)
            return ""
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                content = self._resolve_urls(f.read())
            self._cached_stylesheets[theme_id] = content
            return content
        except Exception as exc:
            logger.error("Error cargando tema legacy '%s': %s", theme_id, exc)
            return ""

    def apply_to(self, app, theme_id: str = None) -> bool:
        qss = self.load_stylesheet(theme_id)
        if not qss:
            return False
        if theme_id:
            self.set_theme(theme_id)
        app.setStyleSheet(qss)
        logger.info("Tema aplicado: %s", self._current_theme)
        return True

    def apply(self, app):
        return self.apply_to(app, self._current_theme)

    def invalidate_cache(self):
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
