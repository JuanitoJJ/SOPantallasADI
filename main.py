import sys
import os
import re
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from core.logger import get_logger
from core.watchdog import crash_handler, watchdog
from core.system_hooks import kiosk
from core.theme_manager import theme_manager
from core.path_utils import get_resource_path
from ui.main_window import MainWindow


logger = get_logger("main")


def load_stylesheet(app):
    """Carga el tema configurado y lo aplica a la aplicación."""
    theme_id = theme_manager.get_current_theme()
    try:
        from core.config_manager import ConfigManager
        config = ConfigManager()
        theme_id = config.get_theme()
    except Exception:
        pass

    qss = theme_manager.load_stylesheet(theme_id)
    if qss:
        app.setStyleSheet(qss)
        theme_manager.set_theme(theme_id)
        logger.info("Hoja de estilos '%s' cargada (%d chars)", theme_id, len(qss))
    else:
        logger.warning("No se pudo cargar el tema '%s'", theme_id)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SOPantallasADI")
    app.setApplicationVersion("2.0.0")

    crash_handler.install()
    crash_handler.start_heartbeat()
    watchdog.start()

    load_stylesheet(app)

    try:
        kiosk.start()
    except Exception as e:
        logger.error("No se pudo iniciar el modo kiosco estricto: %s", e)
        logger.warning("Asegúrate de ejecutar como Administrador para bloquear teclas del sistema.")

    window = MainWindow()
    window.show()

    exit_code = app.exec()

    logger.info("Aplicación finalizando (código %d)", exit_code)
    crash_handler.stop_heartbeat()
    watchdog.stop()
    try:
        kiosk.stop()
    except Exception:
        pass

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
