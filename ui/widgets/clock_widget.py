from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QFont, QFontDatabase

from core.theme_manager import theme_manager
from ui.widgets import apply_text_outline


def _resolve_mono_font(family: str) -> QFont:
    families = QFontDatabase.families()
    if family and family in families:
        return QFont(family)
    for fallback in ("Cascadia Mono", "Cascadia Code", "Consolas", "Courier New"):
        if fallback in families:
            return QFont(fallback)
    return QFont("Monospace")


class ClockWidget(QWidget):
    def __init__(self, parent=None, show_date: bool = True):
        super().__init__(parent)
        self._tokens = theme_manager.current_tokens()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.clock_label = QLabel()
        self.clock_label.setObjectName("ClockLabel")
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        clock_font = _resolve_mono_font(self._tokens.font_family_mono)
        clock_font.setPointSizeF(self._tokens.type_display * 0.75)
        clock_font.setWeight(self._tokens.weight_bold)
        clock_font.setStyleHint(QFont.StyleHint.Monospace)
        clock_font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
        self.clock_label.setFont(clock_font)
        apply_text_outline(self.clock_label)
        layout.addWidget(self.clock_label)

        self.date_label = None
        if show_date:
            self.date_label = QLabel()
            self.date_label.setObjectName("DateLabel")
            self.date_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            date_font = QFont(self._tokens.font_family_body)
            date_font.setPointSizeF(self._tokens.type_xl * 0.75)
            date_font.setWeight(self._tokens.weight_regular)
            self.date_label.setFont(date_font)
            apply_text_outline(self.date_label)
            layout.addWidget(self.date_label)

        theme_manager.register_listener(self._on_theme_changed)

    def _on_theme_changed(self, theme_id: str):
        self._tokens = theme_manager.current_tokens()
        clock_font = _resolve_mono_font(self._tokens.font_family_mono)
        clock_font.setPointSizeF(self._tokens.type_display * 0.75)
        clock_font.setWeight(self._tokens.weight_bold)
        clock_font.setStyleHint(QFont.StyleHint.Monospace)
        clock_font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
        self.clock_label.setFont(clock_font)
        if self.date_label is not None:
            date_font = QFont(self._tokens.font_family_body)
            date_font.setPointSizeF(self._tokens.type_xl * 0.75)
            date_font.setWeight(self._tokens.weight_regular)
            self.date_label.setFont(date_font)

    def update(self):
        now = QDateTime.currentDateTime()
        self.clock_label.setText(now.toString("HH:mm"))
        if self.date_label is not None:
            self.date_label.setText(now.toString("dddd, d 'de' MMMM").capitalize())
