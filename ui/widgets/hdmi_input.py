"""
hdmi_input.py — Card "Compartir pantalla" para el grid de apps.

Botón especial (no es una app .exe) que al pulsarlo abre la ventana
flotante de captura HDMI. Se integra al final del grid cuando
hdmi_input.enabled está activo en config.
"""
from PyQt6.QtWidgets import (QPushButton, QVBoxLayout, QLabel, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from ui.widgets import apply_text_outline
from ui.animations import fade_in


class HDMIInputCard(QPushButton):
    """Card visual que abre el viewer HDMI al hacer click."""

    clicked_hdmi = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AppButton")
        self.setFixedSize(110, 110)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.icon_label = QLabel("🖥️")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet(
            "color: white; font-size: 32px; background: transparent;"
        )
        self.icon_label.setMinimumHeight(45)
        layout.addWidget(self.icon_label, 1)

        self.name_label = QLabel("Compartir pantalla")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet(
            "color: white; font-size: 12px; font-weight: 600; background: transparent;"
        )
        apply_text_outline(self.name_label)
        layout.addWidget(self.name_label)

        self.subtitle_label = QLabel("HDMI Input")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setStyleSheet(
            "color: rgba(255,255,255,0.6); font-size: 9px; "
            "font-style: italic; background: transparent;"
        )
        apply_text_outline(self.subtitle_label, blur_radius=1)
        layout.addWidget(self.subtitle_label)

        self.clicked.connect(self._on_click)

    def _on_click(self):
        self.flash()
        self.clicked_hdmi.emit()

    def flash(self):
        self.setProperty("flash", True)
        self.style().unpolish(self)
        self.style().polish(self)
        QTimer.singleShot(220, lambda: self._clear_flash())

    def _clear_flash(self):
        self.setProperty("flash", False)
        self.style().unpolish(self)
        self.style().polish(self)