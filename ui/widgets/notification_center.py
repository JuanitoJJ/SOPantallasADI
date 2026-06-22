from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QWidget
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from core.notification_manager import (
    notification_manager, Notification, NotificationLevel
)
from core.logger import get_logger


logger = get_logger("ui.widgets.notification_center")


LEVEL_STYLES = {
    NotificationLevel.INFO: ("ℹ", "#3498db"),
    NotificationLevel.WARNING: ("⚠", "#f39c12"),
    NotificationLevel.ERROR: ("✕", "#e74c3c"),
    NotificationLevel.SUCCESS: ("✓", "#27ae60"),
    NotificationLevel.MEETING: ("📅", "#464eb8"),
}


class NotificationCenterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        self.setWindowTitle("Centro de Notificaciones")
        self.setMinimumSize(520, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #1e2a38;
            }
            QLabel {
                color: #ecf0f1;
            }
            QPushButton {
                background-color: #34495e;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2c3e50;
            }
            QPushButton:pressed {
                background-color: #1a252f;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setStyleSheet("background-color: #2c3e50; padding: 12px;")
        header_layout = QHBoxLayout(header)

        title = QLabel("Centro de Notificaciones")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)

        header_layout.addStretch()

        self.unread_label = QLabel("")
        self.unread_label.setStyleSheet("color: #f39c12; font-weight: bold;")
        header_layout.addWidget(self.unread_label)

        layout.addWidget(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background-color: #1e2a38; }")
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background-color: #1e2a38;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(12, 12, 12, 12)
        self.scroll_layout.setSpacing(8)
        self.scroll_layout.addStretch()
        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll, 1)

        footer = QFrame()
        footer.setStyleSheet("background-color: #2c3e50; padding: 10px;")
        footer_layout = QHBoxLayout(footer)

        mark_read_btn = QPushButton("Marcar todas como leídas")
        mark_read_btn.clicked.connect(self._mark_all_read)
        footer_layout.addWidget(mark_read_btn)

        footer_layout.addStretch()

        clear_btn = QPushButton("Borrar historial")
        clear_btn.setStyleSheet(
            "QPushButton { background-color: #c0392b; }"
            "QPushButton:hover { background-color: #a93226; }"
        )
        clear_btn.clicked.connect(self._clear_history)
        footer_layout.addWidget(clear_btn)

        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)

        layout.addWidget(footer)

    def refresh(self):
        while self.scroll_layout.count() > 1:
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        history = notification_manager.get_history()
        unread = notification_manager.get_unread_count()

        if unread > 0:
            self.unread_label.setText(f"{unread} sin leer")
        else:
            self.unread_label.setText("")

        if not history:
            empty = QLabel("Sin notificaciones")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: #7f8c8d; font-style: italic; padding: 40px;")
            self.scroll_layout.insertWidget(0, empty)
            return

        for notif in history:
            card = self._create_notification_card(notif)
            self.scroll_layout.insertWidget(0, card)

    def _create_notification_card(self, notif: Notification) -> QFrame:
        card = QFrame()
        opacity = "1.0" if notif.read else "1.0"
        border = "rgba(243, 156, 18, 0.6)" if not notif.read else "transparent"
        card.setStyleSheet(
            f"QFrame {{ background-color: #2c3e50; border-radius: 8px; "
            f"border-left: 4px solid {border}; }}"
        )

        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        icon, color = LEVEL_STYLES.get(notif.level, LEVEL_STYLES[NotificationLevel.INFO])
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"color: {color}; font-size: 18px; background: transparent;")
        icon_label.setFixedWidth(28)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignTop)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        title_row = QHBoxLayout()
        title = QLabel(notif.title)
        title.setStyleSheet("color: white; font-weight: bold; font-size: 13px;")
        title.setWordWrap(True)
        title_row.addWidget(title, 1)

        time_lbl = QLabel(notif.time_str())
        time_lbl.setStyleSheet("color: #95a5a6; font-size: 11px;")
        title_row.addWidget(time_lbl, 0, Qt.AlignmentFlag.AlignRight)
        text_layout.addLayout(title_row)

        if notif.message:
            msg = QLabel(notif.message)
            msg.setStyleSheet("color: #bdc3c7; font-size: 12px;")
            msg.setWordWrap(True)
            text_layout.addWidget(msg)

        if notif.action_callback and notif.action_label:
            btn = QPushButton(notif.action_label)
            btn.setStyleSheet(
                "QPushButton { background-color: #3498db; color: white; "
                "padding: 4px 10px; font-size: 11px; margin-top: 4px; "
                "max-width: 140px; }"
                "QPushButton:hover { background-color: #2980b9; }"
            )
            btn.clicked.connect(notif.action_callback)
            text_layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignLeft)

        layout.addLayout(text_layout, 1)
        return card

    def _mark_all_read(self):
        notification_manager.mark_all_read()
        self.refresh()

    def _clear_history(self):
        notification_manager.clear()
        self.refresh()


class NotificationBell(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("NotificationBell")
        self.setText("🔔")
        self.setFixedSize(60, 60)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_style()
        self.clicked.connect(self._on_clicked)
        notification_manager.add_listener(self._on_new_notification)

    def _update_style(self):
        unread = notification_manager.get_unread_count()
        color = "#f39c12" if unread > 0 else "#aaaaaa"
        self.setStyleSheet(f"""
            QPushButton#NotificationBell {{
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 30px;
                color: {color};
                font-size: 24px;
            }}
            QPushButton#NotificationBell:hover {{
                background-color: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}
            QPushButton#NotificationBell:pressed {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
        """)

    def _on_new_notification(self, _):
        self._update_style()

    def _on_clicked(self):
        dlg = NotificationCenterDialog(self)
        dlg.exec()
        self._update_style()
