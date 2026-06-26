from PyQt6.QtWidgets import QSlider, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from core.volume_manager import set_system_volume, get_current_volume
from core.theme_manager import theme_manager


class VolumeControl(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tokens = theme_manager.current_tokens()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(self._tokens.space_2)

        self.label = QLabel("VOLUMEN")
        self.label.setObjectName("VolumeLabel")
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        font = QFont(self._tokens.font_family_body)
        font.setPointSizeF(self._tokens.type_md * 0.75)
        font.setWeight(self._tokens.weight_semibold)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.5)
        self.label.setFont(font)
        layout.addWidget(self.label)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(get_current_volume())
        self.slider.setFixedWidth(260)
        self.slider.valueChanged.connect(self._on_change)
        layout.addWidget(self.slider)

        theme_manager.register_listener(self._on_theme_changed)

    def _on_theme_changed(self, theme_id: str):
        self._tokens = theme_manager.current_tokens()
        font = QFont(self._tokens.font_family_body)
        font.setPointSizeF(self._tokens.type_md * 0.75)
        font.setWeight(self._tokens.weight_semibold)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.5)
        self.label.setFont(font)

    def _on_change(self, value: int):
        set_system_volume(value)
