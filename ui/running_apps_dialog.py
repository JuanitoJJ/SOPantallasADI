import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QScrollArea, QWidget, QGridLayout,
                             QGraphicsOpacityEffect, QFrame)
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon
from core.app_launcher import get_running_apps, bring_app_to_front, close_single_app


class RunningAppsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aplicaciones en Ejecución")
        self.setMinimumSize(800, 500)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setObjectName("RunningAppsDialog")

        # Efecto de Opacidad para Animación de Entrada
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)

        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(400)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.animation.start()
        self.animation.finished.connect(lambda: self.setGraphicsEffect(None))

        self.setStyleSheet("""
            #RunningAppsDialog {
                background-color: #1a1a1a;
                border: 2px solid #3d3d3d;
            }
            QLabel#DialogTitle {
                color: white;
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 10px;
            }
            QPushButton#CloseDialogButton {
                background-color: #d83b01;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton#CloseDialogButton:hover {
                background-color: #ef4411;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel("Aplicaciones Abiertas")
        title.setObjectName("DialogTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.grid = QGridLayout(self.container)
        self.grid.setSpacing(20)

        self.refresh_list()

        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, 1)

        # Botón Volver
        close_btn = QPushButton("VOLVER AL MENÚ")
        close_btn.setObjectName("CloseDialogButton")
        close_btn.setMinimumHeight(56)
        close_btn.setMinimumWidth(200)
        close_btn.clicked.connect(self.close)

        layout.addSpacing(20)
        layout.addWidget(close_btn)

    def refresh_list(self):
        """Limpia el grid y lo repinta con las apps actualmente en ejecución."""
        # Limpiar widgets anteriores
        for i in reversed(range(self.grid.count())):
            item = self.grid.itemAt(i)
            w = item.widget() if item else None
            if w:
                w.setParent(None)

        # Obtener lista de apps configuradas del MainWindow (parent)
        configured_apps = []
        if self.parent() and hasattr(self.parent(), 'config_manager'):
            configured_apps = self.parent().config_manager.get_apps()

        running_apps = get_running_apps(configured_apps)

        if not running_apps:
            no_apps = QLabel("No hay aplicaciones abiertas.")
            no_apps.setStyleSheet("font-size: 18px; color: #bdc3c7; font-weight: normal;")
            no_apps.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid.addWidget(no_apps, 0, 0)
            return

        row, col = 0, 0
        for item in running_apps:
            app_info = item['app_info']
            pid = item['process'].pid

            # Contenedor relativo para superponer el botón ×
            card = QWidget()
            card.setFixedSize(160, 160)
            card.setStyleSheet("background: transparent;")

            # Botón principal de la app (traer al frente)
            app_btn = QPushButton(app_info['name'])
            app_btn.setObjectName("AppButton")
            app_btn.setFixedSize(160, 160)
            app_btn.setStyleSheet("""
                QPushButton#AppButton {
                    background-color: #2d2d2d;
                    color: white;
                    border: 2px solid #3d3d3d;
                    border-radius: 10px;
                    padding: 10px;
                    font-size: 14px;
                    text-align: center;
                }
                QPushButton#AppButton:hover {
                    background-color: #3d3d3d;
                    border-color: #0078d7;
                }
                QPushButton#AppButton:pressed {
                    background-color: #0078d7;
                }
            """)
            app_btn.setParent(card)
            app_btn.move(0, 0)

            icon_path = app_info.get('icon', '')
            if icon_path and os.path.exists(icon_path):
                app_btn.setIcon(QIcon(icon_path))
                app_btn.setIconSize(QSize(72, 72))

            app_btn.clicked.connect(lambda checked, p=pid, path=app_info.get('path'): self._switch_to_app(p, path))

            # Botón × (cerrar individualmente) — superpuesto en la esquina superior derecha
            close_app_btn = QPushButton("×")
            close_app_btn.setFixedSize(32, 32)
            close_app_btn.setParent(card)
            close_app_btn.move(128, 0)   # esquina superior derecha de la tarjeta 160×160
            close_app_btn.setStyleSheet("""
                QPushButton {
                    background-color: #c0392b;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 18px;
                    font-weight: bold;
                    padding: 0px;
                }
                QPushButton:pressed {
                    background-color: #96281b;
                }
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
        """Cierra la app y refresca la lista sin cerrar el diálogo."""
        close_single_app(pid)
        self.refresh_list()
