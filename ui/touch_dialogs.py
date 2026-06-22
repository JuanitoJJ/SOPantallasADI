"""
touch_dialogs.py — Diálogos personalizados optimizados para pantalla táctil.

Todos los botones tienen un mínimo de 120×56px y fuentes grandes para
facilitar la interacción sin ratón en pantallas de kiosco corporativo.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QSizePolicy, QGridLayout, QWidget
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont


# ─────────────────────────────────────────────
#  Diálogo de confirmación genérico
# ─────────────────────────────────────────────
class TouchConfirmDialog(QDialog):
    """
    Diálogo de confirmación con dos botones grandes táctiles.
    Devuelve True si el usuario confirma, False si cancela.
    """

    def __init__(self, title: str, message: str,
                 confirm_text: str = "Confirmar",
                 cancel_text: str = "Cancelar",
                 danger: bool = False,
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint
        )
        self.setModal(True)
        self.setMinimumWidth(480)
        self._build_ui(title, message, confirm_text, cancel_text, danger)

    def _build_ui(self, title, message, confirm_text, cancel_text, danger):
        self.setStyleSheet("""
            QDialog {
                background-color: #1e2a38;
                border: 2px solid #34495e;
                border-radius: 16px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(20)

        # Título
        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet(
            "color: #ecf0f1; font-size: 22px; font-weight: bold;"
        )
        layout.addWidget(title_lbl)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #34495e;")
        layout.addWidget(sep)

        # Mensaje
        msg_lbl = QLabel(message)
        msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet(
            "color: #bdc3c7; font-size: 18px; padding: 8px 0;"
        )
        layout.addWidget(msg_lbl)

        layout.addSpacing(8)

        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(16)

        cancel_btn = QPushButton(cancel_text)
        cancel_btn.setMinimumSize(140, 56)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c3e50;
                color: #bdc3c7;
                border: 2px solid #34495e;
                border-radius: 10px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: #34495e;
                color: #ecf0f1;
            }
        """)
        cancel_btn.clicked.connect(self.reject)

        confirm_color = "#c0392b" if danger else "#27ae60"
        confirm_pressed = "#a93226" if danger else "#1e8449"
        confirm_btn = QPushButton(confirm_text)
        confirm_btn.setMinimumSize(140, 56)
        confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {confirm_color};
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:pressed {{
                background-color: {confirm_pressed};
            }}
        """)
        confirm_btn.clicked.connect(self.accept)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(confirm_btn)
        layout.addLayout(btn_layout)


# ─────────────────────────────────────────────
#  Numpad táctil reutilizable
# ─────────────────────────────────────────────
_NUMPAD_BTN_STYLE = """
    QPushButton {{
        background-color: {bg};
        color: {fg};
        border: 2px solid #34495e;
        border-radius: 10px;
        font-size: 22px;
        font-weight: bold;
        min-width: 72px;
        min-height: 72px;
    }}
    QPushButton:pressed {{
        background-color: {bg_pressed};
    }}
    QPushButton:disabled {{
        background-color: #1a252f;
        color: #4a5568;
        border-color: #2c3e50;
    }}
"""

_KEY_STYLE     = _NUMPAD_BTN_STYLE.format(bg="#2c3e50", fg="#ecf0f1", bg_pressed="#3d566e")
_DELETE_STYLE  = _NUMPAD_BTN_STYLE.format(bg="#4a2020", fg="#e74c3c", bg_pressed="#6b2c2c")
_ENTER_STYLE   = _NUMPAD_BTN_STYLE.format(bg="#1a4a2e", fg="#27ae60", bg_pressed="#1e6b3e")


class TouchNumpad(QWidget):
    """
    Numpad táctil 3×4 (dígitos 1-9, *, 0, #).
    Escribe en un QLineEdit de solo lectura asociado.
    Emite una señal 'entered' al pulsar Intro/Aceptar (botón verde).

    Layout:
        7  8  9
        4  5  6
        1  2  3
        ⌫  0  ✓
    """

    def __init__(self, line_edit: QLineEdit, max_length: int = 20, parent=None):
        super().__init__(parent)
        self._input = line_edit
        self._max_length = max_length
        self._build()

    def _build(self):
        grid = QGridLayout(self)
        grid.setSpacing(8)
        grid.setContentsMargins(0, 0, 0, 0)

        keys = [
            ("7", 0, 0), ("8", 0, 1), ("9", 0, 2),
            ("4", 1, 0), ("5", 1, 1), ("6", 1, 2),
            ("1", 2, 0), ("2", 2, 1), ("3", 2, 2),
            ("⌫", 3, 0), ("0", 3, 1), ("✓", 3, 2),
        ]

        for label, row, col in keys:
            btn = QPushButton(label)
            if label == "⌫":
                btn.setStyleSheet(_DELETE_STYLE)
                btn.clicked.connect(self._delete)
            elif label == "✓":
                btn.setStyleSheet(_ENTER_STYLE)
                btn.clicked.connect(self._confirm)
                self._confirm_btn = btn
            else:
                btn.setStyleSheet(_KEY_STYLE)
                btn.clicked.connect(self._make_digit_handler(label))
            grid.addWidget(btn, row, col)

    def _make_digit_handler(self, digit: str):
        def handler():
            current = self._input.text()
            if len(current) < self._max_length:
                self._input.setText(current + digit)
        return handler

    def _delete(self):
        self._input.setText(self._input.text()[:-1])

    def _confirm(self):
        # El botón ✓ activa el returnPressed del QLineEdit
        self._input.returnPressed.emit()

    def set_enabled(self, enabled: bool):
        for btn in self.findChildren(QPushButton):
            btn.setEnabled(enabled)


# ─────────────────────────────────────────────
#  Teclado Alfanumérico táctil
# ─────────────────────────────────────────────
class TouchAlphanumericKeyboard(QWidget):
    """
    Teclado alfanumérico táctil.
    Escribe en un QLineEdit asociado.
    """

    def __init__(self, line_edit: QLineEdit, max_length: int = 32, parent=None):
        super().__init__(parent)
        self._input = line_edit
        self._max_length = max_length
        self._is_caps = True
        self._build()

    def _build(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(6)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Filas del teclado
        rows = [
            ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
            ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
            ["A", "S", "D", "F", "G", "H", "J", "K", "L", "Ñ"],
            ["Z", "X", "C", "V", "B", "N", "M", ",", ".", "-"],
            ["⌫", "ESPACIO", "✓"]
        ]

        for row_keys in rows:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(6)
            for key in row_keys:
                btn = QPushButton(key)
                if key == "⌫":
                    btn.setStyleSheet(_DELETE_STYLE)
                    btn.setMinimumWidth(100)
                    btn.clicked.connect(self._delete)
                elif key == "✓":
                    btn.setStyleSheet(_ENTER_STYLE)
                    btn.setMinimumWidth(100)
                    btn.clicked.connect(self._confirm)
                elif key == "ESPACIO":
                    btn.setStyleSheet(_KEY_STYLE)
                    btn.setMinimumWidth(200)
                    btn.clicked.connect(lambda: self._type(" "))
                else:
                    btn.setStyleSheet(_KEY_STYLE)
                    btn.clicked.connect(self._make_key_handler(key))
                row_layout.addWidget(btn)
            self.main_layout.addLayout(row_layout)

    def _make_key_handler(self, key: str):
        return lambda: self._type(key)

    def _type(self, text: str):
        current = self._input.text()
        if len(current) < self._max_length:
            self._input.setText(current + text)

    def _delete(self):
        self._input.setText(self._input.text()[:-1])

    def _confirm(self):
        self._input.returnPressed.emit()

    def set_enabled(self, enabled: bool):
        for btn in self.findChildren(QPushButton):
            btn.setEnabled(enabled)


# ─────────────────────────────────────────────
#  Diálogo de login Admin táctil
# ─────────────────────────────────────────────
class TouchAdminLoginDialog(QDialog):
    """
    Diálogo de login de administrador optimizado para táctil.
    - Campo de contraseña de solo lectura rellenable con el teclado alfanumérico
    - Teclado físico también funciona (para uso en escritorio)
    - Contador de intentos fallidos con bloqueo temporal de 60s
    """
    MAX_ATTEMPTS = 3
    LOCKOUT_SECONDS = 60

    def __init__(self, correct_password: str, parent=None):
        super().__init__(parent)
        self.correct_password = correct_password
        self._attempts = 0
        self._locked = False
        self.setWindowTitle("Acceso Administrador")
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint
        )
        self.setModal(True)
        self.setMinimumWidth(800) # Más ancho para el teclado alfanumérico
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #1e2a38;
                border: 2px solid #34495e;
                border-radius: 16px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(14)

        # ── Título ──────────────────────────────────────────────────────
        title = QLabel("Acceso Administrador")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "color: #ecf0f1; font-size: 22px; font-weight: bold;"
        )
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #34495e;")
        layout.addWidget(sep)

        # ── Campo contraseña ─────────────────────────────────────────────
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(58)
        self.password_input.setPlaceholderText("Introduce la contraseña")
        self.password_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.password_input.setStyleSheet("""
            QLineEdit {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 2px solid #34495e;
                border-radius: 8px;
                font-size: 26px;
                padding: 8px 14px;
                letter-spacing: 6px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
            QLineEdit:disabled {
                background-color: #1a252f;
                color: #4a5568;
            }
        """)
        self.password_input.returnPressed.connect(self._check_password)
        layout.addWidget(self.password_input)

        # ── Mensaje de estado ────────────────────────────────────────────
        self.status_lbl = QLabel("")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_lbl.setStyleSheet(
            "color: #e74c3c; font-size: 14px; min-height: 20px;"
        )
        layout.addWidget(self.status_lbl)

        # ── Teclado Alfanumérico táctil ──────────────────────────────────
        self.keyboard = TouchAlphanumericKeyboard(self.password_input, max_length=32)
        layout.addWidget(self.keyboard)

        layout.addSpacing(6)

        # ── Botón Cancelar ───────────────────────────────────────────────
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setMinimumHeight(52)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c3e50;
                color: #bdc3c7;
                border: 2px solid #34495e;
                border-radius: 10px;
                font-size: 17px;
                font-weight: bold;
            }
            QPushButton:pressed { background-color: #34495e; }
        """)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

    # ── Validación ──────────────────────────────────────────────────────
    def _check_password(self):
        if self._locked:
            return
        if self.password_input.text() == self.correct_password:
            self.accept()
        else:
            self._attempts += 1
            remaining = self.MAX_ATTEMPTS - self._attempts
            if remaining > 0:
                self.status_lbl.setText(
                    f"Contraseña incorrecta. Intentos restantes: {remaining}"
                )
                self.password_input.clear()
                self.password_input.setFocus()
            else:
                self._start_lockout()

    def _start_lockout(self):
        self._locked = True
        self.keyboard.set_enabled(False)
        self.password_input.setEnabled(False)
        self._countdown = self.LOCKOUT_SECONDS

        self._lockout_timer = QTimer(self)
        self._lockout_timer.timeout.connect(self._tick_lockout)
        self._lockout_timer.start(1000)
        self._tick_lockout()

    def _tick_lockout(self):
        self.status_lbl.setText(
            f"Demasiados intentos. Espera {self._countdown}s..."
        )
        self._countdown -= 1
        if self._countdown < 0:
            self._lockout_timer.stop()
            self._locked = False
            self._attempts = 0
            self.keyboard.set_enabled(True)
            self.password_input.setEnabled(True)
            self.password_input.clear()
            self.password_input.setFocus()
            self.status_lbl.setText("Puedes intentarlo de nuevo.")
