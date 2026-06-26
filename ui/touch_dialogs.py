"""
touch_dialogs.py — Diálogos personalizados optimizados para pantalla táctil.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QSizePolicy, QGridLayout, QWidget
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from core.theme_manager import theme_manager


class TouchConfirmDialog(QDialog):
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
        t = theme_manager.current_tokens()
        self.setStyleSheet(
            f"QDialog {{ background-color: {t.surface_raised}; "
            f"border: 2px solid {t.border_strong}; "
            f"border-radius: {t.dialog_radius}px; }}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            t.space_7, t.space_6, t.space_7, t.space_6
        )
        layout.setSpacing(t.space_4)

        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont(t.font_family_display)
        title_font.setPointSizeF(t.type_lg * 0.75)
        title_font.setBold(True)
        title_lbl.setFont(title_font)
        title_lbl.setStyleSheet(f"color: {t.text_primary}; background: transparent;")
        layout.addWidget(title_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {t.border_subtle}; background: {t.border_subtle}; max-height: 1px;")
        layout.addWidget(sep)

        msg_lbl = QLabel(message)
        msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_lbl.setWordWrap(True)
        msg_font = QFont(t.font_family_body)
        msg_font.setPointSizeF(t.type_md * 0.75)
        msg_lbl.setFont(msg_font)
        msg_lbl.setStyleSheet(
            f"color: {t.text_secondary}; background: transparent; "
            f"padding: {t.space_2}px 0;"
        )
        layout.addWidget(msg_lbl)

        layout.addSpacing(t.space_2)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(t.space_4)

        cancel_btn = QPushButton(cancel_text)
        cancel_btn.setMinimumSize(160, 64)
        cancel_cancel_font = QFont(t.font_family_body)
        cancel_cancel_font.setPointSizeF(t.type_md * 0.75)
        cancel_cancel_font.setBold(True)
        cancel_btn.setFont(cancel_cancel_font)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t.surface_overlay};
                color: {t.text_secondary};
                border: 2px solid {t.border_strong};
                border-radius: {t.control_radius}px;
            }}
            QPushButton:pressed {{
                background-color: {t.surface_raised};
                color: {t.text_primary};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        confirm_color = t.danger if danger else t.success
        confirm_btn = QPushButton(confirm_text)
        confirm_btn.setMinimumSize(160, 64)
        confirm_font = QFont(t.font_family_body)
        confirm_font.setPointSizeF(t.type_md * 0.75)
        confirm_font.setBold(True)
        confirm_btn.setFont(confirm_font)
        confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {confirm_color};
                color: {t.text_on_accent};
                border: none;
                border-radius: {t.control_radius}px;
            }}
            QPushButton:pressed {{
                opacity: 0.85;
            }}
        """)
        confirm_btn.clicked.connect(self.accept)
        btn_layout.addWidget(confirm_btn)

        layout.addLayout(btn_layout)


_NUMPAD_BTN_STYLE = """
    QPushButton {{
        background-color: {bg};
        color: {fg};
        border: 2px solid {border};
        border-radius: {radius}px;
        font-size: {fs}px;
        font-weight: {fw};
        min-width: 72px;
        min-height: 72px;
    }}
    QPushButton:pressed {{
        background-color: {bg_pressed};
    }}
    QPushButton:disabled {{
        background-color: {disabled_bg};
        color: {disabled_fg};
        border-color: {disabled_border};
    }}
"""


def _key_style(t, kind: str) -> str:
    if kind == "key":
        return _NUMPAD_BTN_STYLE.format(
            bg=t.surface_overlay, fg=t.text_primary, border=t.border_strong,
            radius=t.control_radius, fs=int(t.type_xl * 0.75), fw=t.weight_bold,
            bg_pressed=t.surface_raised,
            disabled_bg=t.surface_base, disabled_fg=t.text_muted,
            disabled_border=t.border_subtle,
        )
    if kind == "delete":
        return _NUMPAD_BTN_STYLE.format(
            bg=t.danger, fg=t.text_on_accent, border=t.danger,
            radius=t.control_radius, fs=int(t.type_xl * 0.75), fw=t.weight_bold,
            bg_pressed=t.accent_pressed,
            disabled_bg=t.surface_base, disabled_fg=t.text_muted,
            disabled_border=t.border_subtle,
        )
    if kind == "enter":
        return _NUMPAD_BTN_STYLE.format(
            bg=t.success, fg=t.text_on_accent, border=t.success,
            radius=t.control_radius, fs=int(t.type_xl * 0.75), fw=t.weight_bold,
            bg_pressed=t.accent_pressed,
            disabled_bg=t.surface_base, disabled_fg=t.text_muted,
            disabled_border=t.border_subtle,
        )
    return ""


class TouchNumpad(QWidget):
    def __init__(self, line_edit: QLineEdit, max_length: int = 20, parent=None):
        super().__init__(parent)
        self._input = line_edit
        self._max_length = max_length
        self._build()

    def _build(self):
        t = theme_manager.current_tokens()
        grid = QGridLayout(self)
        grid.setSpacing(t.space_2)
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
                btn.setStyleSheet(_key_style(t, "delete"))
                btn.clicked.connect(self._delete)
            elif label == "✓":
                btn.setStyleSheet(_key_style(t, "enter"))
                btn.clicked.connect(self._confirm)
                self._confirm_btn = btn
            else:
                btn.setStyleSheet(_key_style(t, "key"))
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
        self._input.returnPressed.emit()

    def set_enabled(self, enabled: bool):
        for btn in self.findChildren(QPushButton):
            btn.setEnabled(enabled)


_SHIFT_STYLE = """
    QPushButton {{
        background-color: {bg};
        color: {fg};
        border: 2px solid {border};
        border-radius: {radius}px;
        font-size: {fs}px;
        font-weight: {fw};
        min-width: 72px;
        min-height: 72px;
    }}
    QPushButton:pressed {{
        background-color: {bg_pressed};
    }}
    QPushButton:checked {{
        background-color: {bg_active};
        color: {fg_active};
        border-color: {border_active};
    }}
"""


class TouchAlphanumericKeyboard(QWidget):
    def __init__(self, line_edit: QLineEdit, max_length: int = 32, parent=None):
        super().__init__(parent)
        self._input = line_edit
        self._max_length = max_length
        self._is_caps = True
        self._letter_buttons = {}
        self._build()

    def _build(self):
        t = theme_manager.current_tokens()
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(t.space_2)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        key_style = _key_style(t, "key")

        rows = [
            [("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5"),
             ("6", "6"), ("7", "7"), ("8", "8"), ("9", "9"), ("0", "0")],
            [("Q", "q"), ("W", "w"), ("E", "e"), ("R", "r"), ("T", "t"),
             ("Y", "y"), ("U", "u"), ("I", "i"), ("O", "o"), ("P", "p")],
            [("A", "a"), ("S", "s"), ("D", "d"), ("F", "f"), ("G", "g"),
             ("H", "h"), ("J", "j"), ("K", "k"), ("L", "l"), ("Ñ", "ñ")],
            [("Z", "z"), ("X", "x"), ("C", "c"), ("V", "v"), ("B", "b"),
             ("N", "n"), ("M", "m"), (",", ","), (".", "."), ("-", "-")],
        ]

        for row_keys in rows:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(t.space_2)
            for upper, lower in row_keys:
                btn = QPushButton(upper)
                btn.setStyleSheet(key_style)
                self._letter_buttons[lower] = btn
                btn.clicked.connect(self._make_key_handler(upper, lower))
                row_layout.addWidget(btn)
            self.main_layout.addLayout(row_layout)

        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(t.space_2)

        shift_style = _SHIFT_STYLE.format(
            bg=t.surface_overlay, fg=t.text_primary,
            border=t.border_strong, radius=t.control_radius,
            fs=int(t.type_xl * 0.75), fw=t.weight_bold,
            bg_pressed=t.surface_raised,
            bg_active=t.accent, fg_active=t.text_on_accent,
            border_active=t.accent_pressed,
        )

        self._shift_btn = QPushButton("⇧")
        self._shift_btn.setStyleSheet(shift_style)
        self._shift_btn.setMinimumWidth(96)
        self._shift_btn.setCheckable(True)
        self._shift_btn.setChecked(True)
        self._shift_btn.setToolTip("Cambiar mayúsculas / minúsculas")
        self._shift_btn.clicked.connect(self._toggle_caps)
        bottom_layout.addWidget(self._shift_btn)

        del_btn = QPushButton("⌫")
        del_btn.setStyleSheet(_key_style(t, "delete"))
        del_btn.setMinimumWidth(110)
        del_btn.setToolTip("Borrar último carácter")
        del_btn.clicked.connect(self._delete)
        bottom_layout.addWidget(del_btn)

        space_btn = QPushButton("ESPACIO")
        space_btn.setStyleSheet(key_style)
        space_btn.setMinimumWidth(220)
        space_btn.clicked.connect(lambda: self._type(" "))
        bottom_layout.addWidget(space_btn)

        enter_btn = QPushButton("✓")
        enter_btn.setStyleSheet(_key_style(t, "enter"))
        enter_btn.setMinimumWidth(110)
        enter_btn.setToolTip("Aceptar")
        enter_btn.clicked.connect(self._confirm)
        bottom_layout.addWidget(enter_btn)

        self.main_layout.addLayout(bottom_layout)

    def _toggle_caps(self):
        self._is_caps = not self._is_caps
        for lower, btn in self._letter_buttons.items():
            btn.setText(lower.upper() if self._is_caps else lower)

    def _make_key_handler(self, upper: str, lower: str):
        return lambda: self._type(upper if self._is_caps else lower)

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


class TouchAdminLoginDialog(QDialog):
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
        self.setMinimumWidth(820)
        self._build_ui()

    def _build_ui(self):
        t = theme_manager.current_tokens()
        self.setStyleSheet(
            f"QDialog {{ background-color: {t.surface_raised}; "
            f"border: 2px solid {t.border_strong}; "
            f"border-radius: {t.dialog_radius}px; }}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            t.space_7, t.space_6, t.space_7, t.space_6
        )
        layout.setSpacing(t.space_3)

        title = QLabel("Acceso Administrador")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont(t.font_family_display)
        title_font.setPointSizeF(t.type_lg * 0.75)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {t.text_primary}; background: transparent;")
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {t.border_subtle}; background: {t.border_subtle}; max-height: 1px;")
        layout.addWidget(sep)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(60)
        self.password_input.setPlaceholderText("Introduce la contraseña")
        self.password_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pw_font = QFont(t.font_family_mono)
        pw_font.setPointSizeF(t.type_2xl * 0.75)
        pw_font.setBold(True)
        self.password_input.setFont(pw_font)
        self.password_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {t.surface_overlay};
                color: {t.text_primary};
                border: 2px solid {t.border_strong};
                border-radius: {t.control_radius}px;
                padding: {t.space_2}px {t.space_3}px;
                letter-spacing: 6px;
            }}
            QLineEdit:focus {{
                border-color: {t.border_focus};
            }}
            QLineEdit:disabled {{
                background-color: {t.surface_base};
                color: {t.text_muted};
            }}
        """)
        self.password_input.returnPressed.connect(self._check_password)
        layout.addWidget(self.password_input)

        self.status_lbl = QLabel("")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_font = QFont(t.font_family_body)
        status_font.setPointSizeF(t.type_sm * 0.75)
        status_font.setBold(True)
        self.status_lbl.setFont(status_font)
        self.status_lbl.setStyleSheet(
            f"color: {t.danger}; background: transparent; min-height: 20px;"
        )
        layout.addWidget(self.status_lbl)

        self.keyboard = TouchAlphanumericKeyboard(self.password_input, max_length=32)
        layout.addWidget(self.keyboard)

        layout.addSpacing(t.space_2)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setMinimumHeight(56)
        cancel_font = QFont(t.font_family_body)
        cancel_font.setPointSizeF(t.type_md * 0.75)
        cancel_font.setBold(True)
        cancel_btn.setFont(cancel_font)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t.surface_overlay};
                color: {t.text_secondary};
                border: 2px solid {t.border_strong};
                border-radius: {t.control_radius}px;
            }}
            QPushButton:pressed {{ background-color: {t.surface_raised}; }}
        """)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

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
            f"Demasiados intentos. Espera {self._countdown}s…"
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
