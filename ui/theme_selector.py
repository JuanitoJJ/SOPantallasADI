from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from core.theme_manager import theme_manager, THEMES


class ThemePreviewCard(QPushButton):
    def __init__(self, theme_id: str, label: str, parent=None):
        super().__init__(parent)
        self.theme_id = theme_id
        self.setObjectName("ThemePreviewCard")
        self.setCheckable(True)
        self.setMinimumSize(200, 130)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        data = THEMES[theme_id]
        self.title = QLabel(data["label"])
        self.title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.title)

        self.description = QLabel(data["description"])
        self.description.setWordWrap(True)
        self.description.setStyleSheet("font-size: 11px;")
        layout.addWidget(self.description)

        self.swatch_layout = QHBoxLayout()
        self.swatch_layout.setSpacing(4)
        self._add_swatches(theme_id)
        layout.addLayout(self.swatch_layout)

        layout.addStretch()

    def _add_swatches(self, theme_id: str):
        colors = self._get_swatch_colors(theme_id)
        for color in colors:
            swatch = QFrame()
            swatch.setFixedSize(28, 28)
            swatch.setStyleSheet(
                f"background-color: {color}; "
                f"border: 1px solid rgba(0,0,0,0.2); "
                f"border-radius: 4px;"
            )
            self.swatch_layout.addWidget(swatch)
        self.swatch_layout.addStretch()

    def _get_swatch_colors(self, theme_id: str) -> list:
        return {
            "dark": ["#1a1a1a", "#2c3e50", "#3498db", "#e74c3c"],
            "light": ["#f5f7fa", "#ffffff", "#1976d2", "#d32f2f"],
            "high_contrast": ["#000000", "#ffff00", "#ffffff", "#ff0000"],
        }.get(theme_id, [])


class ThemeSelectorDialog(QDialog):
    theme_selected = pyqtSignal(str)

    def __init__(self, current_theme: str, parent=None):
        super().__init__(parent)
        self.current_theme = current_theme
        self.selected_theme = current_theme
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Seleccionar Tema")
        self.setMinimumSize(680, 280)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Elige un tema para la aplicación")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)
        self._cards = {}

        for theme_id, label, description in theme_manager.get_available_themes():
            card = ThemePreviewCard(theme_id, label)
            card.setToolTip(description)
            card.clicked.connect(lambda checked, tid=theme_id: self._on_card_clicked(tid))
            self._cards[theme_id] = card
            cards_layout.addWidget(card)

        layout.addLayout(cards_layout)

        note = QLabel("El cambio se aplica inmediatamente y se guarda automáticamente.")
        note.setStyleSheet("color: gray; font-style: italic; font-size: 12px;")
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(note)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        apply_btn = QPushButton("Cerrar")
        apply_btn.setObjectName("PrimaryButton")
        apply_btn.setMinimumHeight(40)
        apply_btn.setMinimumWidth(120)
        apply_btn.clicked.connect(self.accept)
        button_layout.addWidget(apply_btn)

        layout.addLayout(button_layout)
        self._refresh_selection()

    def _on_card_clicked(self, theme_id: str):
        self.selected_theme = theme_id
        self._refresh_selection()
        self.theme_selected.emit(theme_id)

    def _refresh_selection(self):
        for tid, card in self._cards.items():
            card.setChecked(tid == self.selected_theme)
            border = "3px solid #3498db" if tid == self.selected_theme else "2px solid transparent"
            card.setStyleSheet(
                f"QPushButton#ThemePreviewCard {{ border: {border}; border-radius: 8px; }}"
            )

    def get_selected_theme(self) -> str:
        return self.selected_theme
