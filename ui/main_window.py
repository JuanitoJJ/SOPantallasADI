import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QGridLayout, 
                             QPushButton, QLabel, QFrame, QSpacerItem, QSizePolicy,
                             QSlider, QHBoxLayout, QMessageBox, QGraphicsOpacityEffect)
from PyQt6.QtCore import Qt, QSize, QTimer, QDateTime, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QColor
from core.config_manager import ConfigManager
from core.app_launcher import launch_application, close_all_launched_apps
from core.volume_manager import set_system_volume, get_current_volume
from ui.admin_login import AdminLoginDialog
from ui.admin_panel import AdminPanelDialog
from ui.running_apps_dialog import RunningAppsDialog
from core.calendar_manager import CalendarManager
from datetime import datetime

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        
        # Inicializar Gestor de Calendario si está habilitado
        self.calendar_manager = None
        if self.config_manager.config.get("calendar_enabled"):
            client_id = self.config_manager.get_client_id()
            tenant_id = self.config_manager.get_tenant_id()
            if client_id:
                self.calendar_manager = CalendarManager(client_id, tenant_id)
        
        self.init_ui()
        
        # Timer para actualizar el reloj cada segundo
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        
        # Timer para actualizar el calendario cada 10 minutos
        if self.calendar_manager:
            self.cal_timer = QTimer(self)
            self.cal_timer.timeout.connect(self.update_calendar)
            self.cal_timer.start(10 * 60 * 1000) # 10 minutos
            self.update_calendar() # Carga inicial

    def init_ui(self):
        # Configuración de ventana
        self.setWindowTitle("Sistema Interactivo Sala de Reuniones")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.showFullScreen()

        # Widget central
        self.central_widget = QWidget()
        self.central_widget.setObjectName("MainLauncher")
        self.setCentralWidget(self.central_widget)

        # Efecto de Opacidad para Animación de Entrada
        self.opacity_effect = QGraphicsOpacityEffect(self.central_widget)
        self.central_widget.setGraphicsEffect(self.opacity_effect)
        
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(800)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation.start()
        self.animation.finished.connect(lambda: self.central_widget.setGraphicsEffect(None))

        # Layout horizontal principal (Apps a la izquierda, Calendario a la derecha)
        self.content_layout = QHBoxLayout(self.central_widget)
        self.content_layout.setContentsMargins(60, 40, 60, 40)
        self.content_layout.setSpacing(40)

        # --- LADO IZQUIERDO: APPS Y CONTROLES ---
        left_panel = QVBoxLayout()
        self.content_layout.addLayout(left_panel, 3)

        # Cabecera / Info de Sala
        self.header = QLabel(self.config_manager.config.get("corporate_name", "SALA DE REUNIONES"))
        self.header.setObjectName("HeaderLabel")
        self.header.setAlignment(Qt.AlignmentFlag.AlignLeft)
        left_panel.addWidget(self.header)

        # Widget de Reloj
        self.clock_label = QLabel()
        self.clock_label.setObjectName("ClockLabel")
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        left_panel.addWidget(self.clock_label)

        # Widget de Fecha
        self.date_label = QLabel()
        self.date_label.setObjectName("DateLabel")
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        left_panel.addWidget(self.date_label)
        
        self.update_time() # Inicializar hora

        # Espaciador
        left_panel.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Contenedor de Apps (Grid)
        self.apps_container = QWidget()
        self.grid_layout = QGridLayout(self.apps_container)
        self.grid_layout.setSpacing(30)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        left_panel.addWidget(self.apps_container, 5)

        self.refresh_apps()

        left_panel.addStretch()

        # --- SECCIÓN DE CONTROLES INFERIORES ---
        controls_layout = QHBoxLayout()
        
        # Control de Volumen
        volume_container = QVBoxLayout()
        vol_label = QLabel("VOLUMEN")
        vol_label.setObjectName("VolumeLabel")
        vol_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(get_current_volume())
        self.volume_slider.setFixedWidth(250)
        self.volume_slider.valueChanged.connect(set_system_volume)
        volume_container.addWidget(vol_label)
        volume_container.addWidget(self.volume_slider)
        controls_layout.addLayout(volume_container)
        
        controls_layout.addStretch()

        self.running_apps_btn = QPushButton("Aplicaciones Abiertas")
        self.running_apps_btn.setObjectName("RunningAppsButton")
        self.running_apps_btn.setMinimumHeight(60)
        self.running_apps_btn.clicked.connect(self.open_running_apps_panel)
        controls_layout.addWidget(self.running_apps_btn)
        
        controls_layout.addSpacing(15)

        self.end_meeting_btn = QPushButton("Finalizar Reunión")
        self.end_meeting_btn.setObjectName("EndMeetingButton")
        self.end_meeting_btn.setMinimumHeight(60)
        self.end_meeting_btn.clicked.connect(self.end_meeting)
        controls_layout.addWidget(self.end_meeting_btn)

        left_panel.addLayout(controls_layout)

        # --- LADO DERECHO: CALENDARIO ---
        if self.calendar_manager:
            right_panel = QVBoxLayout()
            self.content_layout.addLayout(right_panel, 1)
            
            cal_title = QLabel("REUNIONES DE HOY")
            cal_title.setObjectName("CalendarTitle")
            cal_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #3498db; margin-top: 20px;")
            right_panel.addWidget(cal_title)
            
            self.meetings_container = QVBoxLayout()
            right_panel.addLayout(self.meetings_container)
            right_panel.addStretch()

        # Botón Admin (esquina inferior derecha)
        self.admin_btn = QPushButton("Admin")
        self.admin_btn.setObjectName("AdminButton")
        self.admin_btn.setFixedSize(60, 30)
        self.admin_btn.clicked.connect(self.open_admin_panel)
        
        # Ponemos el admin en el layout izquierdo al fondo
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        footer_layout.addWidget(self.admin_btn)
        left_panel.addLayout(footer_layout)

    def update_time(self):
        now = QDateTime.currentDateTime()
        self.clock_label.setText(now.toString("HH:mm"))
        self.date_label.setText(now.toString("dddd, d 'de' MMMM").capitalize())

    def update_calendar(self):
        if not self.calendar_manager:
            return
            
        # Limpiar anterior
        for i in reversed(range(self.meetings_container.count())): 
            widget = self.meetings_container.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                
        meetings = self.calendar_manager.get_upcoming_meetings()
        
        if not meetings:
            no_meetings = QLabel("No hay más reuniones para hoy.")
            no_meetings.setStyleSheet("color: #888; font-style: italic; font-size: 16px; margin-top: 10px;")
            self.meetings_container.addWidget(no_meetings)
            return

        for mtg in meetings[:5]: # Mostrar máximo 5
            card = QFrame()
            card.setObjectName("MeetingCard")
            card.setStyleSheet("""
                #MeetingCard {
                    background-color: #2c3e50;
                    border-radius: 10px;
                    padding: 10px;
                    margin-bottom: 5px;
                }
            """)
            card_layout = QVBoxLayout(card)
            
            subject = QLabel(mtg.get('subject', 'Sin Título'))
            subject.setStyleSheet("color: white; font-weight: bold; font-size: 16px;")
            subject.setWordWrap(True)
            
            # Formatear horas
            try:
                # La API devuelve UTC, podríamos convertir a local, pero simplificamos tomando la parte horaria
                start_str = mtg['start']['dateTime'].split('T')[1][:5]
                end_str = mtg['end']['dateTime'].split('T')[1][:5]
                time_label = QLabel(f"{start_str} - {end_str}")
                time_label.setStyleSheet("color: #bdc3c7; font-size: 14px;")
            except:
                time_label = QLabel("Hora no disponible")

            card_layout.addWidget(subject)
            card_layout.addWidget(time_label)
            self.meetings_container.addWidget(card)

    def refresh_apps(self):
        for i in reversed(range(self.grid_layout.count())): 
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        apps = self.config_manager.get_apps()
        row, col = 0, 0
        max_cols = 3

        for app in apps:
            btn = QPushButton(app['name'])
            btn.setObjectName("AppButton")
            
            icon_path = app.get('icon', '')
            if icon_path and os.path.exists(icon_path):
                btn.setIcon(QIcon(icon_path))
                btn.setIconSize(QSize(100, 100))
            
            btn.clicked.connect(lambda checked, a=app: launch_application(a))
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
        login = AdminLoginDialog(self.config_manager.get_admin_password(), self)
        if login.exec():
            panel = AdminPanelDialog(self.config_manager, self)
            panel.exec()
            # Reiniciar app si cambió algo del calendario
            if self.config_manager.config.get("calendar_enabled") and not self.calendar_manager:
                client_id = self.config_manager.get_client_id()
                tenant_id = self.config_manager.get_tenant_id()
                if client_id:
                    self.calendar_manager = CalendarManager(client_id, tenant_id)
                    # Re-inicializar UI para mostrar el panel de calendario
                    self.init_ui()
            
            self.refresh_apps()

    def open_running_apps_panel(self):
        dialog = RunningAppsDialog(self)
        dialog.exec()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            event.ignore()
        else:
            super().keyPressEvent(event)
