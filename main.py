import sys
import os
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from core.system_hooks import kiosk

def load_stylesheet(app):
    qss_path = os.path.join("ui", "styles", "corporate.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    else:
        print(f"Advertencia: No se encontró el archivo de estilos en {qss_path}")

def main():
    # Inicializar la aplicación PyQt
    app = QApplication(sys.argv)
    
    # Cargar estilos corporativos
    load_stylesheet(app)

    # Iniciar modo kiosco (bloqueo de teclas)
    # NOTA: Puede requerir privilegios de administrador para funcionar correctamente
    try:
        kiosk.start()
    except Exception as e:
        print(f"No se pudo iniciar el modo kiosco estricto: {e}")
        print("Asegúrate de ejecutar como Administrador para bloquear teclas del sistema.")

    # Mostrar ventana principal
    window = MainWindow()
    window.show()

    # Ejecutar el loop de la aplicación
    exit_code = app.exec()
    
    # Liberar teclas al salir
    kiosk.stop()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
