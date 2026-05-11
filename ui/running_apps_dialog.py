import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QScrollArea, QWidget, QGridLayout,
                             QGraphicsOpacityEffect)
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon
from core.app_launcher import get_running_apps, bring_app_to_front

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
        
        # Conectar el final de la animación para limpiar el efecto y evitar glitches
        self.animation.finished.connect(lambda: self.setGraphicsEffect(None))

        # Estilo
        self.setStyleSheet("""
            #RunningAppsDialog {
                background-color: #1a1a1a;
                border: 2px solid #3d3d3d;
            }
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 10px;
            }
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
            QPushButton#CloseButton {
                background-color: #d83b01;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton#CloseButton:hover {
                background-color: #ef4411;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel("Aplicaciones Abiertas")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Scroll Area para las apps
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self.grid = QGridLayout(container)
        self.grid.setSpacing(20)
        
        self.refresh_list()
        
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        # Botón Cerrar
        close_btn = QPushButton("VOLVER AL MENÚ")
        close_btn.setObjectName("CloseButton")
        close_btn.setMinimumHeight(50)
        close_btn.clicked.connect(self.close)
        
        layout.addSpacing(20)
        layout.addWidget(close_btn)

    def refresh_list(self):
        running_apps = get_running_apps()
        
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
            
            btn = QPushButton(app_info['name'])
            btn.setObjectName("AppButton")
            btn.setFixedSize(160, 160)
            
            icon_path = app_info.get('icon', '')
            if icon_path and os.path.exists(icon_path):
                btn.setIcon(QIcon(icon_path))
                btn.setIconSize(QSize(80, 80))
            
            # He eliminado la sombra individual para evitar conflictos con la animación
            
            btn.clicked.connect(lambda checked, p=pid: self.switch_to_app(p))
            self.grid.addWidget(btn, row, col)
            
            col += 1
            if col > 3:
                col = 0
                row += 1

    def switch_to_app(self, pid):
        bring_app_to_front(pid)
        self.accept()
