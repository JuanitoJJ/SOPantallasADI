from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QWidget
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from core.notification_manager import (
    notification_manager, Notification, NotificationLevel
)
from core.theme_manager import theme_manager
from core.logger import get_logger


logger = get_logger("ui.widgets.notification_center")


LEVEL_GLYPHS = {
    NotificationLevel.INFO: "ℹ",
    NotificationLevel.WARNING: "⚠",
    NotificationLevel.ERROR: "✕",
    NotificationLevel.SUCCESS: "✓",
    NotificationLevel.MEETING: "📅",
}


def _level_color(level: NotificationLevel) -> str:
    t = theme_manager.current_tokens()
    return {
        NotificationLevel.INFO: t.info,
        NotificationLevel.WARNING: t.warning,
        NotificationLevel.ERROR: t.danger,
        NotificationLevel.SUCCESS: t.success,
        NotificationLevel.MEETING: t.meeting,
    }.get(level, t.info)


class NotificationCenterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tokens = theme_manager.current_tokens()
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        self.setWindowTitle("Centro de Notificaciones")
        self.setMinimumSize(540, 620)
        t = self._tokens

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setObjectName("AdminHeader")
        header_layout = QHBoxLayout(header)

        title = QLabel("Centro de Notificaciones")
        title_font = QFont(t.font_family_display)
        title_font.setPointSizeF(t.type_lg * 0.75)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("background: transparent;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        self.unread_label = QLabel("")
        self.unread_label.setObjectName("StatusWarn")
        header_layout.addWidget(self.unread_label)

        layout.addWidget(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setObjectName("AdminScrollArea")
        self.scroll_content = QWidget()
        self._scroll_layout = QVBoxLayout(self.scroll_content)
        self._scroll_layout.setContentsMargins(t.space_3, t.space_3, t.space_3, t.space_3)
        self._scroll_layout.setSpacing(t.space_2)
        self._scroll_layout.addStretch()
        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll, 1)

        footer = QFrame()
        footer.setObjectName("AdminFooter")
        footer_layout = QHBoxLayout(footer)

        mark_read_btn = QPushButton("Marcar todas como leídas")
        mark_read_btn.setMinimumHeight(t.button_min_height - 8)
        mark_read_btn.clicked.connect(self._mark_all_read)
        footer_layout.addWidget(mark_read_btn)

        footer_layout.addStretch()

        clear_btn = QPushButton("Borrar historial")
        clear_btn.setObjectName("DangerButton")
        clear_btn.setMinimumHeight(t.button_min_height - 8)
        clear_btn.clicked.connect(self._clear_history)
        footer_layout.addWidget(clear_btn)

        close_btn = QPushButton("Cerrar")
        close_btn.setObjectName("PrimaryButton")
        close_btn.setMinimumHeight(t.button_min_height - 8)
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)

        layout.addWidget(footer)

    def refresh(self):
        while self._scroll_layout.count() > 1:
            item = self._scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        history = notification_manager.get_history()
        unread = notification_manager.get_unread_count()
        t = self._tokens

        if unread > 0:
            self.unread_label.setText(f"  {unread} sin leer  ")
        else:
            self.unread_label.setText("")

        if not history:
            empty = QLabel("Sin notificaciones")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(
                f"color: {t.text_muted}; font-style: italic; "
                f"font-size: {t.type_md}px; padding: {t.space_7}px;"
            )
            self._scroll_layout.insertWidget(0, empty)
            return

        for notif in history:
            card = self._create_notification_card(notif)
            self._scroll_layout.insertWidget(0, card)

    def _create_notification_card(self, notif: Notification) -> QFrame:
        t = self._tokens
        card = QFrame()
        card.setObjectName("Section")
        border_color = t.warning if not notif.read else "transparent"
        card.setStyleSheet(
            f"QFrame#Section {{ border-left: 4px solid {border_color}; }}"
        )

        layout = QHBoxLayout(card)
        layout.setContentsMargins(t.space_3, t.space_2, t.space_3, t.space_2)
        layout.setSpacing(t.space_3)

        glyph = LEVEL_GLYPHS.get(notif.level, LEVEL_GLYPHS[NotificationLevel.INFO])
        color = _level_color(notif.level)
        icon_label = QLabel(glyph)
        icon_label.setStyleSheet(f"color: {color}; font-size: 18px; background: transparent;")
        icon_label.setFixedWidth(28)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignTop)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        title_row = QHBoxLayout()
        title = QLabel(notif.title)
        title.setStyleSheet(
            f"color: {t.text_primary}; font-weight: {t.weight_bold}; "
            f"font-size: {t.type_sm}px;"
        )
        title.setWordWrap(True)
        title_row.addWidget(title, 1)

        time_lbl = QLabel(notif.time_str())
        time_lbl.setStyleSheet(
            f"color: {t.text_muted}; font-size: {t.type_xs}px;"
        )
        title_row.addWidget(time_lbl, 0, Qt.AlignmentFlag.AlignRight)
        text_layout.addLayout(title_row)

        if notif.message:
            msg = QLabel(notif.message)
            msg.setStyleSheet(
                f"color: {t.text_secondary}; font-size: {t.type_xs}px;"
            )
            msg.setWordWrap(True)
            text_layout.addWidget(msg)

        if notif.action_callback and notif.action_label:
            btn = QPushButton(notif.action_label)
            btn.setObjectName("PrimaryButton")
            btn.setMaximumWidth(180)
            btn.setMinimumHeight(36)
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
        self._tokens = theme_manager.current_tokens()
        self.setObjectName("NotificationBell")
        self.setText("🔔")
        self.setFixedSize(56, 56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_style()
        self.clicked.connect(self._on_clicked)
        notification_manager.add_listener(self._on_new_notification)
        theme_manager.register_listener(lambda _: self._update_style())

    def _update_style(self):
        unread = notification_manager.get_unread_count()
        color = self._tokens.warning if unread > 0 else self._tokens.text_muted
        self.setStyleSheet(f"""
            QPushButton#NotificationBell {{
                color: {color};
                font-size: 24px;
            }}
        """)

    def _on_new_notification(self, _):
        self._update_style()

    def _on_clicked(self):
        dlg = NotificationCenterDialog(self)
        dlg.exec()
        self._update_style()
