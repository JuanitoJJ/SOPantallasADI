from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect


def apply_text_outline(label: QLabel, color: str = "#000000", blur_radius: int = 2) -> None:
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur_radius)
    shadow.setColor(QColor(color))
    shadow.setOffset(0, 0)
    label.setGraphicsEffect(shadow)
    if not hasattr(label, "_effects_list"):
        label._effects_list = []
    label._effects_list.append(shadow)
