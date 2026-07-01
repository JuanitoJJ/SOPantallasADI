from PyQt6.QtWidgets import QSlider, QLabel, QVBoxLayout, QHBoxLayout, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from core.volume_manager import set_system_volume, get_current_volume
from core.theme_manager import theme_manager


class VolumeControl(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tokens = theme_manager.current_tokens()
        self.setObjectName("VolumeControl")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            self._tokens.space_4, self._tokens.space_3,
            self._tokens.space_4, self._tokens.space_3
        )
        layout.setSpacing(self._tokens.space_2)

        header_row = QHBoxLayout()
        header_row.setSpacing(self._tokens.space_2)

        self.icon_label = QLabel("\U0001F50A")
        self.icon_label.setObjectName("VolumeIcon")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_font = QFont(self._tokens.font_family_body)
        icon_font.setPointSizeF(self._tokens.type_xl)
        self.icon_label.setFont(icon_font)
        header_row.addWidget(self.icon_label)

        self.label = QLabel("VOLUMEN")
        self.label.setObjectName("VolumeLabel")
        self.label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        font = QFont(self._tokens.font_family_body)
        font.setPointSizeF(self._tokens.type_sm)
        font.setWeight(self._tokens.weight_bold)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2.0)
        self.label.setFont(font)
        header_row.addWidget(self.label)
        header_row.addStretch()

        layout.addLayout(header_row)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(get_current_volume())
        self.slider.setFixedWidth(260)
        self.slider.valueChanged.connect(self._on_change)
        layout.addWidget(self.slider)

        theme_manager.register_listener(self._on_theme_changed)

    def _on_theme_changed(self, theme_id: str):
        self._tokens = theme_manager.current_tokens()
        icon_font = QFont(self._tokens.font_family_body)
        icon_font.setPointSizeF(self._tokens.type_xl)
        self.icon_label.setFont(icon_font)
        font = QFont(self._tokens.font_family_body)
        font.setPointSizeF(self._tokens.type_sm)
        font.setWeight(self._tokens.weight_bold)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2.0)
        self.label.setFont(font)

    def _on_change(self, value: int):
        set_system_volume(value)
