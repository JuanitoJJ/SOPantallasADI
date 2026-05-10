from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, QFileDialog, 
                             QLineEdit, QFormLayout, QMessageBox, QCheckBox, QTabWidget, QWidget)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import os

from core.icon_utils import extract_and_save_icon
from core.calendar_manager import CalendarManager

class CalendarAuthWorker(QThread):
    finished = pyqtSignal(bool, str)
    
    def __init__(self, manager, flow):
        super().__init__()
        self.manager = manager
        self.flow = flow
        
    def run(self):
        try:
            success = self.manager.complete_device_flow(self.flow)
            if success:
                self.finished.emit(True, "Conexión establecida con éxito.")
            else:
                self.finished.emit(False, "No se pudo completar la conexión.")
        except Exception as e:
            self.finished.emit(False, f"Error durante la conexión: {e}")

class AdminPanelDialog(QDialog):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Panel de Control - Administrador")
        self.resize(800, 600)

        self.main_layout = QVBoxLayout(self)
        
        # Tab Widget
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        # TAB 1: GESTIÓN DE APPS
        self.apps_tab = QWidget()
        self.setup_apps_tab()
        self.tabs.addTab(self.apps_tab, "Aplicaciones")

        # TAB 2: CALENDARIO M365
        self.calendar_tab = QWidget()
        self.setup_calendar_tab()
        self.tabs.addTab(self.calendar_tab, "Calendario M365")

        # Botón para cerrar la aplicación completamente (fuera de los tabs)
        self.exit_app_btn = QPushButton("Cerrar Kiosco y Volver a Windows")
        self.exit_app_btn.setStyleSheet("background-color: #e74c3c; color: white; margin-top: 10px; padding: 10px; font-weight: bold;")
        self.exit_app_btn.clicked.connect(self.exit_kiosk)
        self.main_layout.addWidget(self.exit_app_btn)

    def setup_apps_tab(self):
        layout = QVBoxLayout(self.apps_tab)
        
        # Lista de aplicaciones
        self.app_list = QListWidget()
        self.refresh_list()
        layout.addWidget(self.app_list)

        # Botones de acción para la lista
        btn_layout = QHBoxLayout()
        self.remove_btn = QPushButton("Eliminar Seleccionada")
        self.remove_btn.clicked.connect(self.remove_selected_app)
        btn_layout.addWidget(self.remove_btn)
        layout.addLayout(btn_layout)

        # Formulario para añadir nueva app
        form_group = QVBoxLayout()
        form_title = QLabel("Añadir Nueva Aplicación")
        form_title.setStyleSheet("font-weight: bold; margin-top: 15px; color: #333;")
        form_group.addWidget(form_title)

        form_layout = QFormLayout()
        self.name_input = QLineEdit()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("C:\\Ruta\\al\\programa.exe")
        
        browse_btn = QPushButton("Examinar...")
        browse_btn.clicked.connect(self.browse_exe)
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_btn)

        form_layout.addRow("Nombre:", self.name_input)
        form_layout.addRow("Ruta EXE:", path_layout)
        form_group.addLayout(form_layout)
        
        add_btn = QPushButton("Añadir Aplicación")
        add_btn.setObjectName("PrimaryButton")
        add_btn.setFixedHeight(45)
        add_btn.clicked.connect(self.add_app)
        form_group.addWidget(add_btn)

        layout.addLayout(form_group)

    def setup_calendar_tab(self):
        layout = QVBoxLayout(self.calendar_tab)
        
        info_label = QLabel("Configuración de Microsoft 365 Calendar")
        info_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        layout.addWidget(info_label)
        
        desc_label = QLabel("Permite mostrar las reuniones de la sala en la pantalla principal.\nRequiere registrar una aplicación en Azure AD (Entra ID).")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        form_layout = QFormLayout()
        
        self.cal_enabled_cb = QCheckBox("Habilitar Calendario")
        self.cal_enabled_cb.setChecked(self.config_manager.config.get("calendar_enabled", False))
        
        self.client_id_input = QLineEdit()
        self.client_id_input.setText(self.config_manager.get_client_id())
        self.client_id_input.setPlaceholderText("Introduce el Client ID de Azure")
        
        self.tenant_id_input = QLineEdit()
        self.tenant_id_input.setText(self.config_manager.get_tenant_id())
        self.tenant_id_input.setPlaceholderText("Introduce el Tenant ID o 'common'")
        
        form_layout.addRow("", self.cal_enabled_cb)
        form_layout.addRow("Client ID:", self.client_id_input)
        form_layout.addRow("Tenant ID:", self.tenant_id_input)
        
        layout.addLayout(form_layout)
        
        # Botón Guardar Config
        save_cal_btn = QPushButton("Guardar Configuración")
        save_cal_btn.clicked.connect(self.save_calendar_config)
        layout.addWidget(save_cal_btn)
        
        layout.addSpacing(20)
        
        # Sección de Vinculación
        auth_group = QVBoxLayout()
        auth_title = QLabel("Vinculación de Cuenta")
        auth_title.setStyleSheet("font-weight: bold; color: #333;")
        auth_group.addWidget(auth_title)
        
        self.link_btn = QPushButton("Iniciar Vinculación (Device Login)")
        self.link_btn.setMinimumHeight(50)
        self.link_btn.clicked.connect(self.start_calendar_auth)
        auth_group.addWidget(self.link_btn)
        
        self.auth_status_label = QLabel("Estado: No vinculado o requiere re-autenticación")
        self.auth_status_label.setStyleSheet("color: #666;")
        auth_group.addWidget(self.auth_status_label)
        
        layout.addLayout(auth_group)
        layout.addStretch()

    def save_calendar_config(self):
        self.config_manager.config["calendar_enabled"] = self.cal_enabled_cb.isChecked()
        self.config_manager.config["client_id"] = self.client_id_input.text()
        self.config_manager.config["tenant_id"] = self.tenant_id_input.text()
        self.config_manager.save_config()
        QMessageBox.information(self, "Configuración Guardada", "Los cambios en el calendario se han guardado.")

    def start_calendar_auth(self):
        client_id = self.client_id_input.text()
        tenant_id = self.tenant_id_input.text() or "common"
        if not client_id:
            QMessageBox.warning(self, "Error", "Debes introducir un Client ID válido.")
            return
            
        try:
            self.cal_manager = CalendarManager(client_id, tenant_id)
            flow = self.cal_manager.initiate_device_flow()
            
            # Mostrar mensaje con el código
            msg = f"1. Ve a: {flow['verification_uri']}\n2. Introduce este código: {flow['user_code']}\n\nEste panel esperará a que completes el inicio de sesión..."
            
            # Usamos un cuadro de mensaje no bloqueante o informamos en el label
            self.auth_status_label.setText(f"CÓDIGO: {flow['user_code']}\nEsperando confirmación...")
            self.auth_status_label.setStyleSheet("color: #0078d7; font-weight: bold; font-size: 16px;")
            
            # Bloquear botón mientras se autentica
            self.link_btn.setEnabled(False)
            self.link_btn.setText("Esperando en Microsoft...")
            
            # Hilo para esperar el token
            self.auth_worker = CalendarAuthWorker(self.cal_manager, flow)
            self.auth_worker.finished.connect(self.on_auth_finished)
            self.auth_worker.start()
            
            QMessageBox.information(self, "Autenticación Iniciada", msg)
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error detallado de autenticación:\n{error_details}")
            QMessageBox.critical(self, "Error de Autenticación", f"No se pudo iniciar el proceso.\n\nDetalle: {str(e)}\n\nRevisa la consola para más detalles.")

    def on_auth_finished(self, success, message):
        self.link_btn.setEnabled(True)
        self.link_btn.setText("Iniciar Vinculación (Device Login)")
        
        if success:
            self.auth_status_label.setText("Estado: Vinculado correctamente")
            self.auth_status_label.setStyleSheet("color: green; font-weight: bold;")
            QMessageBox.information(self, "Éxito", message)
        else:
            self.auth_status_label.setText("Estado: Fallo en la vinculación")
            self.auth_status_label.setStyleSheet("color: red;")
            QMessageBox.warning(self, "Error", message)

    def refresh_list(self):
        self.app_list.clear()
        for app in self.config_manager.get_apps():
            item = QListWidgetItem(f"{app['name']}")
            item.setToolTip(app['path'])
            self.app_list.addItem(item)

    def browse_exe(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Ejecutable", "C:\\Program Files", "Executables (*.exe)")
        if file_path:
            clean_path = file_path.replace("/", "\\")
            self.path_input.setText(clean_path)
            if not self.name_input.text():
                name = os.path.splitext(os.path.basename(clean_path))[0]
                self.name_input.setText(name)

    def add_app(self):
        name = self.name_input.text()
        path = self.path_input.text()
        if name and path:
            icon_path = extract_and_save_icon(path)
            self.config_manager.add_app(name, path, icon_path)
            self.refresh_list()
            self.name_input.clear()
            self.path_input.clear()
            QMessageBox.information(self, "Éxito", f"Aplicación '{name}' añadida con éxito.")
        else:
            QMessageBox.warning(self, "Error", "Debes completar nombre y ruta")

    def remove_selected_app(self):
        current_row = self.app_list.currentRow()
        if current_row >= 0:
            self.config_manager.remove_app(current_row)
            self.refresh_list()
        else:
            QMessageBox.warning(self, "Error", "Selecciona una aplicación para eliminar")

    def exit_kiosk(self):
        reply = QMessageBox.question(self, 'Confirmar', '¿Estás seguro de que quieres salir del sistema de kiosco?', 
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            from PyQt6.QtWidgets import QApplication
            QApplication.quit()
