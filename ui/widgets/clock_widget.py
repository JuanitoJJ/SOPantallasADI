from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget, QSizePolicy
from PyQt6.QtCore import Qt, QDateTime, QLocale
from PyQt6.QtGui import QFont, QFontMetrics

from core.theme_manager import theme_manager


SPANISH_LOCALE = QLocale(QLocale.Language.Spanish)


class ClockWidget(QWidget):
    def __init__(self, parent=None, show_date: bool = True):
        super().__init__(parent)
        self._tokens = theme_manager.current_tokens()
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(self._tokens.space_1)

        self.date_label = None
        if show_date:
            self.date_label = QLabel()
            self.date_label.setObjectName("DateLabel")
            self.date_label.setAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            date_font = QFont(self._tokens.font_family_body)
            date_font.setPointSizeF(self._tokens.type_date)
            date_font.setWeight(self._tokens.weight_regular)
            self.date_label.setFont(date_font)
            layout.addWidget(self.date_label)

        self.clock_label = QLabel()
        self.clock_label.setObjectName("ClockLabel")
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.clock_label.setFont(self._build_clock_font())
        self._apply_stable_width()
        layout.addWidget(self.clock_label)

        theme_manager.register_listener(self._on_theme_changed)

    def _build_clock_font(self) -> QFont:
        font = QFont(self._tokens.font_family_display)
        font.setPointSizeF(self._tokens.type_clock)
        font.setWeight(QFont.Weight.Bold)
        return font

    def _apply_stable_width(self):
        fm = QFontMetrics(self.clock_label.font())
        width = fm.horizontalAdvance("00:00:00") + self._tokens.space_1
        self.clock_label.setMinimumWidth(width)

    def _on_theme_changed(self, theme_id: str):
        self._tokens = theme_manager.current_tokens()
        self.clock_label.setFont(self._build_clock_font())
        self._apply_stable_width()
        if self.date_label is not None:
            date_font = QFont(self._tokens.font_family_body)
            date_font.setPointSizeF(self._tokens.type_date)
            date_font.setWeight(self._tokens.weight_regular)
            self.date_label.setFont(date_font)

    def update(self):
        now = QDateTime.currentDateTime()
        self.clock_label.setText(now.toString("HH:mm:ss"))
        if self.date_label is not None:
            self.date_label.setText(
                SPANISH_LOCALE.toString(now, "dddd, d 'de' MMMM").capitalize()
            )
