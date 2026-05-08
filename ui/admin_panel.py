from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, QFileDialog, 
                             QLineEdit, QFormLayout, QMessageBox)
from PyQt6.QtCore import Qt

class AdminPanelDialog(QDialog):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Panel de Control - Administrador")
        self.resize(600, 450)

        layout = QVBoxLayout(self)

        # Título
        title = QLabel("Gestión de Aplicaciones")
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

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
        form_title.setStyleSheet("font-weight: bold; margin-top: 15px;")
        form_group.addWidget(form_title)

        form_layout = QFormLayout()
        self.name_input = QLineEdit()
        self.path_input = QLineEdit()
        
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
        add_btn.clicked.connect(self.add_app)
        form_group.addWidget(add_btn)

        layout.addLayout(form_group)

        # Botón para cerrar la aplicación completamente
        exit_app_btn = QPushButton("Cerrar Kiosco y Volver a Windows")
        exit_app_btn.setStyleSheet("background-color: #e74c3c; color: white; margin-top: 20px;")
        exit_app_btn.clicked.connect(self.exit_kiosk)
        layout.addWidget(exit_app_btn)

    def refresh_list(self):
        self.app_list.clear()
        for app in self.config_manager.get_apps():
            self.app_list.addItem(f"{app['name']} ({app['path']})")

    def browse_exe(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Ejecutable", "", "Executables (*.exe)")
        if file_path:
            self.path_input.setText(file_path.replace("/", "\\"))

    def add_app(self):
        name = self.name_input.text()
        path = self.path_input.text()

        if name and path:
            self.config_manager.add_app(name, path)
            self.refresh_list()
            self.name_input.clear()
            self.path_input.clear()
            QMessageBox.information(self, "Éxito", "Aplicación añadida correctamente")
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
