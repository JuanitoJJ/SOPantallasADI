import os

from PyQt6.QtGui import QFont, QFontDatabase

from core.path_utils import get_resource_path
from core.logger import get_logger

logger = get_logger("core.font_loader")

INTER_FAMILY = "Inter"


def load_bundled_fonts() -> list:
    fonts_dir = get_resource_path("assets/fonts")
    loaded = []
    candidates = []

    if os.path.isdir(fonts_dir):
        for name in sorted(os.listdir(fonts_dir)):
            if not name.lower().endswith((".ttf", ".otf")):
                continue
            path = os.path.join(fonts_dir, name)
            font_id = QFontDatabase.addApplicationFont(path)
            if font_id < 0:
                logger.warning("No se pudo cargar la fuente: %s", path)
                continue
            families = QFontDatabase.applicationFontFamilies(font_id)
            loaded.extend(families)
            candidates.extend(families)
            logger.info("Fuente cargada: %s -> %s", name, families)
    else:
        logger.warning("Directorio de fuentes no encontrado: %s", fonts_dir)

    available = QFontDatabase.families()
    if INTER_FAMILY not in available:
        for fam in candidates:
            if fam and fam != INTER_FAMILY:
                QFont.insertSubstitution(INTER_FAMILY, fam)
                logger.info("Substitución de fuente: %s -> %s", INTER_FAMILY, fam)
                break
        else:
            logger.warning(
                "La familia '%s' no está disponible; se usará el fallback del sistema.",
                INTER_FAMILY,
            )

    return loaded
