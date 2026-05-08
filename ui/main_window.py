import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QGridLayout, 
                             QPushButton, QLabel, QFrame, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from core.config_manager import ConfigManager
from core.app_launcher import launch_application
from ui.admin_login import AdminLoginDialog
from ui.admin_panel import AdminPanelDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.init_ui()

    def init_ui(self):
        # Configuración de ventana
        self.setWindowTitle("Sistema Kiosco Corporativo")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.showFullScreen()

        # Widget central
        self.central_widget = QWidget()
        self.central_widget.setObjectName("MainLauncher")
        self.setCentralWidget(self.central_widget)

        # Layout principal
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        self.main_layout.setSpacing(20)

        # Cabecera
        self.header = QLabel(self.config_manager.config.get("corporate_name", "MI EMPRESA"))
        self.header.setObjectName("HeaderLabel")
        self.header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.header)

        # Espaciador
        self.main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Contenedor de Apps (Grid)
        self.apps_container = QWidget()
        self.grid_layout = QGridLayout(self.apps_container)
        self.grid_layout.setSpacing(30)
        self.main_layout.addWidget(self.apps_container, 5)

        self.refresh_apps()

        # Espaciador inferior
        self.main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Botón Admin oculto (en la esquina inferior derecha)
        self.admin_btn = QPushButton("Admin")
        self.admin_btn.setObjectName("AdminButton")
        self.admin_btn.setFixedSize(80, 40)
        self.admin_btn.clicked.connect(self.open_admin_panel)
        
        # Lo ponemos en la esquina inferior derecha usando un layout horizontal
        footer_layout = QVBoxLayout()
        footer_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        footer_layout.addWidget(self.admin_btn)
        self.main_layout.addLayout(footer_layout)

    def refresh_apps(self):
        # Limpiar grid actual
        for i in reversed(range(self.grid_layout.count())): 
            self.grid_layout.itemAt(i).widget().setParent(None)

        apps = self.config_manager.get_apps()
        row, col = 0, 0
        max_cols = 4 if len(apps) > 4 else 3

        for app in apps:
            btn = QPushButton(app['name'])
            btn.setObjectName("AppButton")
            
            # Intentar cargar icono si existe
            if os.path.exists(app.get('icon', '')):
                btn.setIcon(QIcon(app['icon']))
                btn.setIconSize(QSize(100, 100))
            
            btn.clicked.connect(lambda checked, a=app: launch_application(a['path']))
            self.grid_layout.addWidget(btn, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def open_admin_panel(self):
        # Primero pedimos contraseña
        login = AdminLoginDialog(self.config_manager.get_admin_password(), self)
        if login.exec():
            # Si la contraseña es correcta, abrimos el panel
            panel = AdminPanelDialog(self.config_manager, self)
            panel.exec()
            # Al cerrar el panel, refrescamos la lista de apps por si hubo cambios
            self.refresh_apps()

    def keyPressEvent(self, event):
        # Evitar que cierren con Esc
        if event.key() == Qt.Key.Key_Escape:
            event.ignore()
        else:
            super().keyPressEvent(event)
