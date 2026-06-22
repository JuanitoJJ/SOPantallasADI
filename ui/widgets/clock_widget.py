from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QDateTime
from ui.widgets import apply_text_outline


class ClockWidget(QWidget):
    def __init__(self, parent=None, show_date: bool = True):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.clock_label = QLabel()
        self.clock_label.setObjectName("ClockLabel")
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        apply_text_outline(self.clock_label)
        layout.addWidget(self.clock_label)

        self.date_label = None
        if show_date:
            self.date_label = QLabel()
            self.date_label.setObjectName("DateLabel")
            self.date_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            apply_text_outline(self.date_label)
            layout.addWidget(self.date_label)

    def update(self):
        now = QDateTime.currentDateTime()
        self.clock_label.setText(now.toString("HH:mm"))
        if self.date_label is not None:
            self.date_label.setText(now.toString("dddd, d 'de' MMMM").capitalize())
