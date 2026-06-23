import json
import os
from dotenv import load_dotenv
from core.logger import get_logger

load_dotenv()

logger = get_logger("core.config_manager")

CONFIG_FILE = "config.json"

DEFAULT_THEME = "dark"


class ConfigManager:
    def __init__(self):
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error("Error cargando config: %s", e)

        default_config = {
            "admin_password": "admin",
            "apps": [
                {
                    "name": "Microsoft Teams",
                    "path": os.path.expandvars(r"%LocalAppData%\Microsoft\WindowsApps\ms-teams.exe"),
                    "icon": "assets/icons/ms-teams.png",
                    "category": "Reuniones",
                }
            ],
            "corporate_name": "SISTEMA CORPORATIVO",
            "calendar_enabled": False,
            "client_id": "",
            "tenant_id": "common",
            "client_secret": "",
            "room_email": "",
            "wallpaper_folder": "assets/wallpapers",
            "wallpaper_interval_seconds": 60,
            "theme": DEFAULT_THEME,
            "notification_sound_enabled": True,
            "notification_sound_path": "",
            "alert_minutes_before_meeting": 5,
        }
        self.save_config(default_config)
        return default_config

    def save_config(self, config=None):
        if config:
            self.config = config
        try:
            if self.config.get("wallpaper_folder") == "assets/wallpapers":
                os.makedirs("assets/wallpapers", exist_ok=True)

            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logger.error("Error guardando config: %s", e)

    def get_wallpaper_settings(self):
        return {
            "folder": self.config.get("wallpaper_folder", "assets/wallpapers"),
            "interval": self.config.get("wallpaper_interval_seconds", 60)
        }

    def get_apps(self):
        return self.config.get("apps", [])

    def get_theme(self) -> str:
        """Retorna el tema configurado (variable de entorno tiene prioridad)."""
        env_theme = os.getenv("THEME")
        if env_theme:
            return env_theme
        return self.config.get("theme", DEFAULT_THEME)

    def set_theme(self, theme_id: str):
        """Cambia el tema y persiste en config."""
        valid_themes = ["dark"]
        if theme_id not in valid_themes:
            logger.warning("Tema inválido '%s', ignorando", theme_id)
            return False
        self.config["theme"] = theme_id
        self.save_config()
        logger.info("Tema guardado en config: %s", theme_id)
        return True

    def get_admin_password(self):
        env_pass = os.getenv("ADMIN_PASSWORD")
        if env_pass:
            return env_pass
        return self.config.get("admin_password", "admin")

    def get_client_id(self):
        env_client = os.getenv("CLIENT_ID")
        if env_client:
            return env_client
        return self.config.get("client_id", "")

    def get_tenant_id(self):
        env_tenant = os.getenv("TENANT_ID")
        if env_tenant:
            return env_tenant
        return self.config.get("tenant_id", "common")

    def get_client_secret(self):
        env_secret = os.getenv("CLIENT_SECRET")
        if env_secret:
            return env_secret
        return self.config.get("client_secret", "")

    def get_room_email(self):
        env_room = os.getenv("ROOM_EMAIL")
        if env_room:
            return env_room
        return self.config.get("room_email", "")

    def add_app(self, name, path, icon="", category=""):
        self.config["apps"].append({
            "name": name,
            "path": path,
            "icon": icon,
            "category": category or "Sin categoría",
        })
        self.save_config()

    def remove_app(self, index):
        if 0 <= index < len(self.config["apps"]):
            self.config["apps"].pop(index)
            self.save_config()

    def move_app(self, index: int, direction: int):
        apps = self.config.get("apps", [])
        new_index = index + direction
        if 0 <= new_index < len(apps):
            apps[index], apps[new_index] = apps[new_index], apps[index]
            self.save_config()

    def set_app_category(self, index: int, category: str):
        apps = self.config.get("apps", [])
        if 0 <= index < len(apps):
            apps[index]["category"] = category
            self.save_config()

    def get_notification_settings(self) -> dict:
        return {
            "sound_enabled": self.config.get("notification_sound_enabled", True),
            "sound_path": self.config.get("notification_sound_path", ""),
            "alert_minutes_before": self.config.get("alert_minutes_before_meeting", 5),
        }

    # ── HDMI Input ─────────────────────────────────────────────
    def get_hdmi_input(self) -> dict:
        """Devuelve la configuración de la entrada HDMI.

        Defaults: enabled=False, device_index=0, 1920x1080 @ 30 fps.
        """
        hdmi = self.config.get("hdmi_input", {})
        return {
            "enabled": hdmi.get("enabled", False),
            "device_index": int(hdmi.get("device_index", 0)),
            "width": int(hdmi.get("width", 1920)),
            "height": int(hdmi.get("height", 1080)),
            "fps": int(hdmi.get("fps", 30)),
        }

    def set_hdmi_input(self, enabled: bool, device_index: int = 0,
                       width: int = 1920, height: int = 1080, fps: int = 30):
        """Guarda la configuración HDMI."""
        self.config["hdmi_input"] = {
            "enabled": bool(enabled),
            "device_index": int(device_index),
            "width": int(width),
            "height": int(height),
            "fps": int(fps),
        }
        self.save_config()

    def is_hdmi_enabled(self) -> bool:
        return bool(self.config.get("hdmi_input", {}).get("enabled", False))
