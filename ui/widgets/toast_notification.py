from PyQt6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton, QHBoxLayout, QVBoxLayout,
    QGraphicsOpacityEffect, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, pyqtSignal
from PyQt6.QtGui import QFont

from core.notification_manager import Notification, NotificationLevel
from core.logger import get_logger


logger = get_logger("ui.widgets.toast_notification")


LEVEL_STYLES = {
    NotificationLevel.INFO: {
        "bg": "#3498db",
        "icon": "ℹ",
        "border": "#2980b9",
    },
    NotificationLevel.WARNING: {
        "bg": "#f39c12",
        "icon": "⚠",
        "border": "#e67e22",
    },
    NotificationLevel.ERROR: {
        "bg": "#e74c3c",
        "icon": "✕",
        "border": "#c0392b",
    },
    NotificationLevel.SUCCESS: {
        "bg": "#27ae60",
        "icon": "✓",
        "border": "#229954",
    },
    NotificationLevel.MEETING: {
        "bg": "#464eb8",
        "icon": "📅",
        "border": "#353a8d",
    },
}

DEFAULT_DURATION_MS = 6000
SLIDE_DURATION_MS = 350
MARGIN = 20


class ToastNotification(QFrame):
    dismissed = pyqtSignal()
    action_clicked = pyqtSignal()

    def __init__(self, notification: Notification, parent=None, duration_ms: int = DEFAULT_DURATION_MS):
        super().__init__(parent)
        self.notification = notification
        self.duration_ms = duration_ms
        self._build()
        self._apply_style()

    def _build(self):
        self.setObjectName("ToastNotification")
        self.setMinimumWidth(360)
        self.setMaximumWidth(420)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        style = LEVEL_STYLES.get(self.notification.level, LEVEL_STYLES[NotificationLevel.INFO])
        self.icon_label = QLabel(style["icon"])
        self.icon_label.setObjectName("ToastIcon")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        font = QFont()
        font.setPointSize(20)
        font.setBold(True)
        self.icon_label.setFont(font)
        self.icon_label.setFixedWidth(32)
        layout.addWidget(self.icon_label, 0, Qt.AlignmentFlag.AlignTop)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        self.title_label = QLabel(self.notification.title)
        self.title_label.setObjectName("ToastTitle")
        self.title_label.setWordWrap(True)
        font_title = QFont()
        font_title.setPointSize(12)
        font_title.setBold(True)
        self.title_label.setFont(font_title)
        text_layout.addWidget(self.title_label)

        if self.notification.message:
            self.message_label = QLabel(self.notification.message)
            self.message_label.setObjectName("ToastMessage")
            self.message_label.setWordWrap(True)
            font_msg = QFont()
            font_msg.setPointSize(10)
            self.message_label.setFont(font_msg)
            text_layout.addWidget(self.message_label)

        if self.notification.action_callback and self.notification.action_label:
            self.action_btn = QPushButton(self.notification.action_label)
            self.action_btn.setObjectName("ToastActionButton")
            self.action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.action_btn.clicked.connect(self._on_action_clicked)
            text_layout.addWidget(self.action_btn)
        else:
            self.action_btn = None

        layout.addLayout(text_layout, 1)

        close_btn = QPushButton("✕")
        close_btn.setObjectName("ToastCloseButton")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.dismiss)
        layout.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignTop)

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self.opacity_effect)

    def _apply_style(self):
        style = LEVEL_STYLES.get(self.notification.level, LEVEL_STYLES[NotificationLevel.INFO])
        self.setStyleSheet(f"""
            #ToastNotification {{
                background-color: {style['bg']};
                border: 2px solid {style['border']};
                border-radius: 10px;
                color: white;
            }}
            #ToastTitle {{
                color: white;
                background: transparent;
                border: none;
            }}
            #ToastMessage {{
                color: rgba(255, 255, 255, 0.9);
                background: transparent;
                border: none;
            }}
            #ToastIcon {{
                color: white;
                background: transparent;
                border: none;
            }}
            #ToastCloseButton {{
                background-color: rgba(0, 0, 0, 0.15);
                color: white;
                border: none;
                border-radius: 14px;
                font-weight: bold;
                font-size: 14px;
            }}
            #ToastCloseButton:hover {{
                background-color: rgba(0, 0, 0, 0.3);
            }}
            #ToastActionButton {{
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.4);
                border-radius: 5px;
                padding: 6px 12px;
                font-weight: bold;
                margin-top: 4px;
            }}
            #ToastActionButton:hover {{
                background-color: rgba(255, 255, 255, 0.3);
            }}
            #ToastActionButton:pressed {{
                background-color: rgba(255, 255, 255, 0.4);
            }}
        """)

    def show_animated(self):
        self.opacity_effect.setOpacity(0.0)
        self.show()
        self.raise_()
        anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        anim.setDuration(SLIDE_DURATION_MS)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        self._fade_in_anim = anim

        if self.duration_ms > 0:
            QTimer.singleShot(self.duration_ms, self.dismiss)

    def dismiss(self):
        if not self.isVisible():
            return
        anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        anim.setDuration(SLIDE_DURATION_MS)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InCubic)
        anim.finished.connect(self._on_dismiss_finished)
        anim.start()
        self._fade_out_anim = anim

    def _on_dismiss_finished(self):
        self.dismissed.emit()
        self.deleteLater()

    def _on_action_clicked(self):
        if self.notification.action_callback:
            try:
                self.notification.action_callback()
            except Exception as exc:
                logger.warning("Error en callback de notificación: %s", exc)
        self.action_clicked.emit()
        self.dismiss()


class ToastContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self._toasts: list = []
        self._spacing = 10

    def show_notification(self, notification: Notification, duration_ms: int = DEFAULT_DURATION_MS):
        toast = ToastNotification(notification, parent=self, duration_ms=duration_ms)
        toast.dismissed.connect(lambda t=toast: self._remove_toast(t))
        self._toasts.append(toast)
        self._relayout()
        toast.show_animated()
        toast.show()
        self._relayout()

    def _remove_toast(self, toast):
        if toast in self._toasts:
            self._toasts.remove(toast)
        self._relayout()

    def _relayout(self):
        if not self.parent():
            return
        parent_rect = self.parent().rect()
        x = parent_rect.width() - 440 - MARGIN
        y = MARGIN
        for toast in self._toasts:
            toast.adjustSize()
            toast.move(x, y)
            y += toast.height() + self._spacing
            toast.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._relayout()
