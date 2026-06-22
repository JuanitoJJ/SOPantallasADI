from PyQt6.QtWidgets import QSlider, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
from core.volume_manager import set_system_volume, get_current_volume


class VolumeControl(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        self.label = QLabel("VOLUMEN")
        self.label.setObjectName("VolumeLabel")
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.label)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(get_current_volume())
        self.slider.setFixedWidth(250)
        self.slider.valueChanged.connect(self._on_change)
        layout.addWidget(self.slider)

    def _on_change(self, value: int):
        set_system_volume(value)
