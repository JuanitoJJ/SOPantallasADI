"""
app_categories.py — Agrupación de aplicaciones por categorías.

Permite organizar las apps del kiosco en categorías como:
- Comunicación (Teams, Outlook)
- Productividad (Office, etc.)
- Navegación (Chrome, Edge)
- Reuniones (Teams, Zoom, etc.)
"""
from core.logger import get_logger
from core.config_manager import ConfigManager


logger = get_logger("core.app_categories")


DEFAULT_CATEGORY = "Sin categoría"
UNCATEGORIZED = "General"


class AppCategoryManager:
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

    def get_all_categories(self, apps: list) -> list:
        """Retorna lista de categorías únicas en uso, más DEFAULT_CATEGORY."""
        categories = set()
        for app in apps:
            cat = app.get("category", DEFAULT_CATEGORY)
            if cat:
                categories.add(cat)
        if not categories:
            categories.add(UNCATEGORIZED)
        return sorted(categories)

    def get_suggested_categories(self) -> list:
        """Lista curada de categorías comunes para sugerir en el admin."""
        return [
            UNCATEGORIZED,
            "Comunicación",
            "Productividad",
            "Navegación",
            "Reuniones",
            "Diseño",
            "Desarrollo",
            "Multimedia",
            "Utilidades",
        ]

    def group_apps(self, apps: list) -> dict:
        """Agrupa apps por categoría. Retorna dict {categoria: [apps]}."""
        groups = {}
        for app in apps:
            cat = app.get("category", DEFAULT_CATEGORY) or UNCATEGORIZED
            groups.setdefault(cat, []).append(app)
        return groups

    def add_category_to_app(self, app: dict, category: str) -> dict:
        """Devuelve una copia del app con la categoría añadida."""
        new_app = dict(app)
        new_app["category"] = category
        return new_app

    def filter_apps_by_category(self, apps: list, category: str) -> list:
        if category == "all" or not category:
            return apps
        return [a for a in apps if a.get("category", DEFAULT_CATEGORY) == category]


app_category_manager = AppCategoryManager()
