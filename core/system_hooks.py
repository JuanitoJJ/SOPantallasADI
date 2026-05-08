import keyboard

class KioskManager:
    def __init__(self):
        self.blocked_keys = [
            'windows', 
            'alt+tab', 
            'ctrl+esc', 
            'alt+f4', 
            'shift+f10', # Menú contextual en algunos casos
            'f11'        # Evitar salir de pantalla completa si se usa un navegador
        ]
        self.is_active = False

    def start(self):
        """Bloquea las teclas del sistema."""
        if not self.is_active:
            for key in self.blocked_keys:
                keyboard.block_key(key)
            self.is_active = True
            print("Modo Kiosco: Teclas bloqueadas.")

    def stop(self):
        """Libera las teclas del sistema."""
        if self.is_active:
            for key in self.blocked_keys:
                keyboard.unblock_key(key)
            self.is_active = False
            print("Modo Kiosco: Teclas liberadas.")

# Instancia global
kiosk = KioskManager()
