import json
import os

CONFIG_FILE = "config.json"

class ConfigManager:
    def __init__(self):
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error cargando config: {e}")
        
        # Configuración por defecto
        default_config = {
            "admin_password": "admin",
            "apps": [
                {
                    "name": "Microsoft Teams",
                    "path": os.path.expandvars(r"%LocalAppData%\Microsoft\Teams\current\Teams.exe"),
                    "icon": "assets/icons/teams.png"
                }
            ],
            "corporate_name": "SISTEMA CORPORATIVO"
        }
        self.save_config(default_config)
        return default_config

    def save_config(self, config=None):
        if config:
            self.config = config
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error guardando config: {e}")

    def get_apps(self):
        return self.config.get("apps", [])

    def get_admin_password(self):
        return self.config.get("admin_password", "admin")
    
    def add_app(self, name, path, icon=""):
        self.config["apps"].append({
            "name": name,
            "path": path,
            "icon": icon
        })
        self.save_config()

    def remove_app(self, index):
        if 0 <= index < len(self.config["apps"]):
            self.config["apps"].pop(index)
            self.save_config()
