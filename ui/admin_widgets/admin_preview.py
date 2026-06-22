from PyQt6.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QSlider,
    QSizePolicy, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from datetime import datetime


class AdminPreviewFrame(QFrame):
    """Mini-preview de la pantalla principal para ver cambios en vivo."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AdminPreview")
        self.setMinimumSize(520, 320)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet(
            "QFrame#AdminPreview {"
            " background-color: #1a1a1a; border: 2px solid #34495e;"
            " border-radius: 8px;"
            "}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)

        self.corp_name_label = QLabel("SALA DE REUNIONES")
        self.corp_name_label.setStyleSheet(
            "color: #ecf0f1; font-size: 14px; font-weight: 300; background: transparent;"
        )
        layout.addWidget(self.corp_name_label)

        self.clock_label = QLabel("12:00")
        clock_font = QFont()
        clock_font.setPointSize(48)
        clock_font.setBold(True)
        self.clock_label.setFont(clock_font)
        self.clock_label.setStyleSheet("color: white; background: transparent;")
        layout.addWidget(self.clock_label)

        self.date_label = QLabel("Lunes, 1 de Enero")
        self.date_label.setStyleSheet(
            "color: #bdc3c7; font-size: 12px; background: transparent;"
        )
        layout.addWidget(self.date_label)

        layout.addSpacing(8)

        apps_row = QHBoxLayout()
        apps_row.setSpacing(6)
        self.app_buttons = []
        for i in range(3):
            btn = QPushButton(f"App {i+1}")
            btn.setFixedSize(80, 80)
            btn.setStyleSheet(
                "QPushButton {"
                " background-color: #2c3e50; color: white; border: 1px solid #34495e;"
                " border-radius: 12px; font-size: 10px; font-weight: 600;"
                "}"
            )
            self.app_buttons.append(btn)
            apps_row.addWidget(btn)
        apps_row.addStretch()

        end_btn = QPushButton("Finalizar")
        end_btn.setStyleSheet(
            "QPushButton {"
            " background-color: #e74c3c; color: white; border: none;"
            " border-radius: 8px; padding: 6px 12px; font-size: 11px; font-weight: bold;"
            "}"
        )
        end_btn.setMinimumHeight(40)
        apps_row.addWidget(end_btn)

        self.running_btn = QPushButton("Abiertas")
        self.running_btn.setStyleSheet(
            "QPushButton {"
            " background-color: #3498db; color: white; border: none;"
            " border-radius: 8px; padding: 6px 12px; font-size: 11px; font-weight: bold;"
            "}"
        )
        self.running_btn.setMinimumHeight(40)
        apps_row.addWidget(self.running_btn)

        layout.addLayout(apps_row)
        layout.addStretch()

        volume_row = QHBoxLayout()
        vol_label = QLabel("Vol:")
        vol_label.setStyleSheet("color: #bdc3c7; font-size: 11px; background: transparent;")
        volume_row.addWidget(vol_label)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setMaximumWidth(200)
        self.volume_slider.setStyleSheet(
            "QSlider::groove:horizontal { background: #2c3e50; height: 6px; border-radius: 3px; }"
            "QSlider::sub-page:horizontal { background: #3498db; border-radius: 3px; }"
            "QSlider::handle:horizontal { background: #3498db; width: 16px; height: 16px; "
            "margin: -5px 0; border-radius: 8px; }"
        )
        volume_row.addWidget(self.volume_slider)
        volume_row.addStretch()

        layout.addLayout(volume_row)

    def update_corporate_name(self, name: str):
        if name:
            self.corp_name_label.setText(name)

    def update_time(self):
        now = datetime.now()
        self.clock_label.setText(now.strftime("%H:%M"))
        try:
            self.date_label.setText(now.strftime("%A, %-d de %B"))
        except ValueError:
            self.date_label.setText(now.strftime("%A, %d de %B").replace(" 0", " "))
