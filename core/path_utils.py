import sys
import os

def get_resource_path(relative_path):
    """
    Obtiene la ruta absoluta de un recurso, compatible con PyInstaller
    y con el entorno de desarrollo.
    """
    try:
        # PyInstaller crea una carpeta temporal y guarda la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
