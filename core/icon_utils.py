import os
from PyQt6.QtWidgets import QFileIconProvider
from PyQt6.QtCore import QFileInfo, QSize
from PyQt6.QtGui import QIcon, QPixmap

def extract_and_save_icon(exe_path, output_folder="assets/icons"):
    """
    Extrae el icono de un archivo .exe y lo guarda como PNG.
    Retorna la ruta del archivo PNG guardado.
    """
    if not os.path.exists(exe_path):
        return ""

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Obtener el nombre base para el archivo de icono
    base_name = os.path.splitext(os.path.basename(exe_path))[0]
    icon_path = os.path.join(output_folder, f"{base_name}.png")

    try:
        # Usar QFileIconProvider para obtener el icono del sistema
        file_info = QFileInfo(exe_path)
        icon_provider = QFileIconProvider()
        icon = icon_provider.icon(file_info)

        if not icon.isNull():
            # Obtener el tamaño más grande disponible (usualmente 256x256 o 128x128)
            pixmap = icon.pixmap(256, 256)
            if pixmap.isNull():
                pixmap = icon.pixmap(QSize(128, 128))
            
            pixmap.save(icon_path, "PNG")
            return icon_path
    except Exception as e:
        print(f"Error extrayendo icono de {exe_path}: {e}")
    
    return ""
