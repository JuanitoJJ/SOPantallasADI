from PyQt6.QtWidgets import (
    QWidget, QPushButton, QGridLayout, QLabel, QVBoxLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, QTimer, QRect, QPropertyAnimation
from PyQt6.QtGui import QIcon
import os
from core.app_launcher import launch_application
from core.path_utils import get_resource_path
from core.theme_manager import theme_manager
from ui.animations import staggered_fade_in, DURATIONS, EASING


class AppCard(QPushButton):
    """Botón de app con icono."""

    def __init__(self, app_info: dict, parent=None):
        super().__init__(parent)
        self.app_info = app_info
        self._tokens = theme_manager.current_tokens()
        self.setObjectName("AppButton")
        self.setFixedSize(110, 110)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(app_info.get("name", ""))
        self.setAccessibleName(app_info.get("name", ""))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            self._tokens.space_3, self._tokens.space_3,
            self._tokens.space_3, self._tokens.space_3
        )
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.icon_label = QLabel()
        self.icon_label.setObjectName("AppIconLabel")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setMinimumHeight(68)
        layout.addWidget(self.icon_label, 1, Qt.AlignmentFlag.AlignCenter)

        self._load_icon()

    def _load_icon(self):
        icon_path = self.app_info.get("icon", "")
        if icon_path:
            full_path = get_resource_path(icon_path)
            if not os.path.exists(full_path):
                full_path = icon_path
            if os.path.exists(full_path):
                pix = QIcon(full_path).pixmap(QSize(56, 56))
                if not pix.isNull():
                    self.icon_label.setPixmap(pix)
                    return
        name = self.app_info.get("name", "?")
        first_letter = name[0].upper() if name else "?"
        self.icon_label.setObjectName("AppIconFallback")
        self.icon_label.setText(first_letter)
        self.style().unpolish(self.icon_label)
        self.style().polish(self.icon_label)

    def flash(self):
        self.setProperty("flash", True)
        self.style().unpolish(self)
        self.style().polish(self)
        QTimer.singleShot(DURATIONS["instant"], self._reset_flash)
        self._animate_scale()

    def _reset_flash(self):
        self.setProperty("flash", False)
        self.style().unpolish(self)
        self.style().polish(self)

    def _animate_scale(self):
        original = self.geometry()
        cx = original.center()
        inset = 6
        start_rect = QRect(
            cx.x() - (original.width() - inset) // 2,
            cx.y() - (original.height() - inset) // 2,
            original.width() - inset,
            original.height() - inset,
        )
        self._flash_anim = QPropertyAnimation(self, b"geometry")
        self._flash_anim.setDuration(DURATIONS["fast"])
        self._flash_anim.setStartValue(start_rect)
        self._flash_anim.setEndValue(original)
        self._flash_anim.setEasingCurve(EASING["out_back"])
        self._flash_anim.start()


class AppGrid(QWidget):
    """Grid de aplicaciones."""

    def __init__(self, apps: list, parent=None, on_launch=None):
        super().__init__(parent)
        self.apps = apps
        self.on_launch = on_launch
        self._cards = []
        self._build()

    def _build(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)

        self.grid_container = QWidget()
        self._grid_layout = QGridLayout(self.grid_container)
        self._grid_layout.setSpacing(24)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        main_layout.addWidget(self.grid_container, 1)

        self._render_apps()

    CARD_SIZE = 110

    def _compute_max_cols(self) -> int:
        available = self.grid_container.width()
        spacing = self._grid_layout.spacing()
        if available <= 0:
            return 5
        cols = available // (self.CARD_SIZE + spacing)
        return max(1, min(5, cols))

    def _render_apps(self):
        for card in self._cards:
            self._grid_layout.removeWidget(card)
            card.setParent(None)
            card.deleteLater()
        self._cards = []

        max_cols = self._compute_max_cols()
        self._last_max_cols = max_cols

        row, col = 0, 0
        new_cards = []
        for idx, app in enumerate(self.apps):
            card = AppCard(app)
            card.clicked.connect(lambda checked, c=card, a=app: self._launch(a, c))
            self._grid_layout.addWidget(card, row, col)
            self._cards.append(card)
            new_cards.append(card)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        staggered_fade_in(new_cards, stagger_ms=DURATIONS["instant"], duration="fast")

    def _relayout_grid(self):
        max_cols = self._compute_max_cols()
        if max_cols == getattr(self, "_last_max_cols", None):
            return
        self._last_max_cols = max_cols
        row, col = 0, 0
        for card in self._cards:
            self._grid_layout.removeWidget(card)
            self._grid_layout.addWidget(card, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._relayout_grid()

    def update_apps(self, apps: list):
        self.apps = apps
        self._render_apps()

    def _launch(self, app_info, card):
        card.flash()
        error = launch_application(app_info)
        if error and self.on_launch:
            self.on_launch(error, app_info)
