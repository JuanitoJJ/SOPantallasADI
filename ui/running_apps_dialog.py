import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QScrollArea, QWidget, QGridLayout,
                             QGraphicsOpacityEffect, QFrame)
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon
from core.app_launcher import get_running_apps, bring_app_to_front, close_single_app
from core.theme_manager import theme_manager


class RunningAppsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tokens = theme_manager.current_tokens()
        self.setWindowTitle("Aplicaciones en Ejecución")
        self.setMinimumSize(800, 500)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setObjectName("RunningAppsDialog")

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)

        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(400)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.animation.start()
        self.animation.finished.connect(lambda: self.setGraphicsEffect(None))

        t = self._tokens
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            t.space_7, t.space_7, t.space_7, t.space_7
        )

        title = QLabel("Aplicaciones Abiertas")
        title.setObjectName("DialogTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.grid = QGridLayout(self.container)
        self.grid.setSpacing(t.space_4)

        self.refresh_list()

        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, 1)

        close_btn = QPushButton("VOLVER AL MENÚ")
        close_btn.setObjectName("CloseDialogButton")
        close_btn.setMinimumHeight(56)
        close_btn.setMinimumWidth(220)
        close_btn.clicked.connect(self.close)

        layout.addSpacing(t.space_4)
        layout.addWidget(close_btn)

    def refresh_list(self):
        for i in reversed(range(self.grid.count())):
            item = self.grid.itemAt(i)
            w = item.widget() if item else None
            if w:
                w.setParent(None)

        configured_apps = []
        if self.parent() and hasattr(self.parent(), 'config_manager'):
            configured_apps = self.parent().config_manager.get_apps()

        running_apps = get_running_apps(configured_apps)
        t = self._tokens

        if not running_apps:
            no_apps = QLabel("No hay aplicaciones abiertas.")
            no_apps.setStyleSheet(
                f"font-size: {t.type_md}px; color: {t.text_muted}; "
                f"font-weight: {t.weight_regular};"
            )
            no_apps.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid.addWidget(no_apps, 0, 0)
            return

        row, col = 0, 0
        for item in running_apps:
            app_info = item['app_info']
            pid = item['process'].pid

            card = QWidget()
            card.setFixedSize(160, 160)
            card.setStyleSheet("background: transparent;")

            app_btn = QPushButton(app_info['name'])
            app_btn.setObjectName("AppButton")
            app_btn.setFixedSize(160, 160)
            app_btn.setStyleSheet(f"""
                QPushButton#AppButton {{
                    background-color: {t.surface_overlay};
                    color: {t.text_primary};
                    border: 1px solid {t.border_subtle};
                    border-radius: {t.card_radius}px;
                    padding: {t.space_3}px;
                    font-size: {t.type_sm}px;
                    text-align: center;
                }}
                QPushButton#AppButton:hover {{
                    background-color: {t.surface_raised};
                    border-color: {t.accent};
                }}
                QPushButton#AppButton:pressed {{
                    background-color: {t.accent};
                    color: {t.text_on_accent};
                }}
            """)
            app_btn.setParent(card)
            app_btn.move(0, 0)

            icon_path = app_info.get('icon', '')
            if icon_path and os.path.exists(icon_path):
                app_btn.setIcon(QIcon(icon_path))
                app_btn.setIconSize(QSize(72, 72))

            app_btn.clicked.connect(
                lambda checked, p=pid, path=app_info.get('path'): self._switch_to_app(p, path)
            )

            close_app_btn = QPushButton("×")
            close_app_btn.setFixedSize(32, 32)
            close_app_btn.setParent(card)
            close_app_btn.move(128, 0)
            close_app_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {t.danger};
                    color: {t.text_on_accent};
                    border: none;
                    border-radius: {t.space_1 + 2}px;
                    font-size: 18px;
                    font-weight: {t.weight_bold};
                    padding: 0px;
                }}
                QPushButton:pressed {{
                    opacity: 0.85;
                }}
            """)
            close_app_btn.clicked.connect(lambda checked, p=pid: self._close_app(p))
            close_app_btn.raise_()

            self.grid.addWidget(card, row, col)

            col += 1
            if col > 3:
                col = 0
                row += 1

    def _switch_to_app(self, pid, path=None):
        bring_app_to_front(pid, path)
        self.accept()

    def _close_app(self, pid):
        close_single_app(pid)
        self.refresh_list()

