from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtCore import Qt

class AdminLoginDialog(QDialog):
    def __init__(self, correct_password, parent=None):
        super().__init__(parent)
        self.correct_password = correct_password
        self.authorized = False
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Acceso Administrador")
        self.setFixedSize(300, 180)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)

        label = QLabel("Ingrese la contraseña de administrador:")
        layout.addWidget(label)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setObjectName("AdminInput")
        layout.addWidget(self.password_input)

        self.login_btn = QPushButton("Acceder")
        self.login_btn.setObjectName("PrimaryButton")
        self.login_btn.clicked.connect(self.check_password)
        layout.addWidget(self.login_btn)

    def check_password(self):
        if self.password_input.text() == self.correct_password:
            self.authorized = True
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Contraseña incorrecta")
            self.password_input.clear()
