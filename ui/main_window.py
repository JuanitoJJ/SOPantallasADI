import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QGridLayout, 
                             QPushButton, QLabel, QFrame, QSpacerItem, QSizePolicy,
                             QSlider, QHBoxLayout, QMessageBox)
from PyQt6.QtCore import Qt, QSize, QTimer, QDateTime
from PyQt6.QtGui import QIcon
from core.config_manager import ConfigManager
from core.app_launcher import launch_application, close_all_launched_apps
from core.volume_manager import set_system_volume, get_current_volume
from ui.admin_login import AdminLoginDialog
from ui.admin_panel import AdminPanelDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.init_ui()
        
        # Timer para actualizar el reloj cada segundo
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)

    def init_ui(self):
        # Configuración de ventana
        self.setWindowTitle("Sistema Interactivo Sala de Reuniones")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.showFullScreen()

        # Widget central
        self.central_widget = QWidget()
        self.central_widget.setObjectName("MainLauncher")
        self.setCentralWidget(self.central_widget)

        # Layout principal
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(60, 40, 60, 40)
        self.main_layout.setSpacing(10)

        # Cabecera / Info de Sala
        self.header = QLabel(self.config_manager.config.get("corporate_name", "SALA DE REUNIONES"))
        self.header.setObjectName("HeaderLabel")
        self.header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.header)

        # Widget de Reloj
        self.clock_label = QLabel()
        self.clock_label.setObjectName("ClockLabel")
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.clock_label)

        # Widget de Fecha
        self.date_label = QLabel()
        self.date_label.setObjectName("DateLabel")
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.date_label)
        
        self.update_time() # Inicializar hora

        # Espaciador
        self.main_layout.addSpacerItem(QSpacerItem(20, 60, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Contenedor de Apps (Grid)
        self.apps_container = QWidget()
        self.grid_layout = QGridLayout(self.apps_container)
        self.grid_layout.setSpacing(40)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.apps_container, 5)

        self.refresh_apps()

        # Espaciador intermedio
        self.main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # --- SECCIÓN DE CONTROLES INFERIORES ---
        controls_layout = QHBoxLayout()

        # Control de Volumen
        volume_container = QVBoxLayout()
        vol_label = QLabel("VOLUMEN")
        vol_label.setObjectName("VolumeLabel")
        vol_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(get_current_volume())
        self.volume_slider.setFixedWidth(300)
        self.volume_slider.valueChanged.connect(set_system_volume)
        
        volume_container.addWidget(vol_label)
        volume_container.addWidget(self.volume_slider)
        controls_layout.addLayout(volume_container)

        controls_layout.addStretch()

        # Botón Finalizar Reunión
        self.end_meeting_btn = QPushButton("Finalizar Reunión")
        self.end_meeting_btn.setObjectName("EndMeetingButton")
        self.end_meeting_btn.setMinimumHeight(60)
        self.end_meeting_btn.clicked.connect(self.end_meeting)
        controls_layout.addWidget(self.end_meeting_btn)

        self.main_layout.addLayout(controls_layout)

        # Botón Admin (esquina inferior derecha, sutil)
        self.admin_btn = QPushButton("Admin")
        self.admin_btn.setObjectName("AdminButton")
        self.admin_btn.setFixedSize(60, 30)
        self.admin_btn.clicked.connect(self.open_admin_panel)
        
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        footer_layout.addWidget(self.admin_btn)
        self.main_layout.addLayout(footer_layout)

    def update_time(self):
        now = QDateTime.currentDateTime()
        self.clock_label.setText(now.toString("HH:mm"))
        # Fecha en español
        self.date_label.setText(now.toString("dddd, d 'de' MMMM").capitalize())

    def refresh_apps(self):
        # Limpiar grid actual
        for i in reversed(range(self.grid_layout.count())): 
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        apps = self.config_manager.get_apps()
        row, col = 0, 0
        max_cols = 4 if len(apps) > 4 else 3

        for app in apps:
            btn = QPushButton(app['name'])
            btn.setObjectName("AppButton")
            
            # Intentar cargar icono si existe
            icon_path = app.get('icon', '')
            if icon_path and os.path.exists(icon_path):
                btn.setIcon(QIcon(icon_path))
                btn.setIconSize(QSize(120, 120))
            
            btn.clicked.connect(lambda checked, a=app: launch_application(a['path']))
            self.grid_layout.addWidget(btn, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def end_meeting(self):
        reply = QMessageBox.question(self, 'Finalizar Reunión', 
                                    '¿Estás seguro de que quieres finalizar la reunión?\nSe cerrarán todas las aplicaciones abiertas.', 
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            close_all_launched_apps()
            QMessageBox.information(self, "Reunión Finalizada", "Se han cerrado las aplicaciones. El sistema está listo.")

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
