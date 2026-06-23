from PyQt6.QtWidgets import (
    QWidget, QPushButton, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout,
    QComboBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon
import os
from core.app_launcher import launch_application
from core.app_categories import app_category_manager, DEFAULT_CATEGORY
from core.path_utils import get_resource_path
from ui.widgets import apply_text_outline
from ui.animations import fade_in


class AppCard(QPushButton):
    """Botón de app con icono, nombre y categoría."""

    def __init__(self, app_info: dict, parent=None):
        super().__init__(parent)
        self.app_info = app_info
        self.setObjectName("AppButton")
        self.setFixedSize(110, 110)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("background: transparent;")
        self.icon_label.setMinimumHeight(45)
        layout.addWidget(self.icon_label, 1)

        self.name_label = QLabel(app_info.get("name", ""))
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet(
            "color: white; font-size: 12px; font-weight: 600; background: transparent;"
        )
        apply_text_outline(self.name_label)
        layout.addWidget(self.name_label)

        category = app_info.get("category", DEFAULT_CATEGORY)
        if category and category != DEFAULT_CATEGORY:
            self.category_label = QLabel(category)
            self.category_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.category_label.setStyleSheet(
                "color: rgba(255,255,255,0.6); font-size: 11px; "
                "font-style: italic; background: transparent;"
            )
            apply_text_outline(self.category_label, blur_radius=1)
            layout.addWidget(self.category_label)
        else:
            self.category_label = None

        self._load_icon()

    def _load_icon(self):
        icon_path = self.app_info.get("icon", "")
        if icon_path:
            full_path = get_resource_path(icon_path)
            if not os.path.exists(full_path):
                full_path = icon_path
            if os.path.exists(full_path):
                pix = QIcon(full_path).pixmap(QSize(45, 45))
                if not pix.isNull():
                    self.icon_label.setPixmap(pix)
                    return
        # Fallback: emoji de la primera letra
        name = self.app_info.get("name", "?")
        first_letter = name[0].upper() if name else "?"
        self.icon_label.setText(first_letter)
        self.icon_label.setStyleSheet(
            "color: white; font-size: 28px; font-weight: bold; background: transparent;"
        )

    def flash(self):
        self.setProperty("flash", True)
        self.style().unpolish(self)
        self.style().polish(self)
        QTimer.singleShot(220, lambda: self._clear_flash())

    def _clear_flash(self):
        self.setProperty("flash", False)
        self.style().unpolish(self)
        self.style().polish(self)


class AppGrid(QWidget):
    """Grid de aplicaciones con filtro por categoría."""

    category_changed = pyqtSignal(str)

    def __init__(self, apps: list, parent=None, on_launch=None,
                 show_category_filter: bool = True):
        super().__init__(parent)
        self.apps = apps
        self.on_launch = on_launch
        self._cards = []
        self._current_category = "all"
        self._show_category_filter = show_category_filter
        self._build()

    def _build(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)

        if self._show_category_filter:
            filter_row = QHBoxLayout()
            filter_lbl = QLabel("Categoría:")
            filter_lbl.setStyleSheet(
                "color: #bdc3c7; font-size: 14px; font-weight: bold;"
            )
            filter_row.addWidget(filter_lbl)

            self.category_combo = QComboBox()
            self.category_combo.setMinimumHeight(36)
            self.category_combo.setMinimumWidth(200)
            self.category_combo.addItem("Todas las categorías", "all")
            categories = app_category_manager.get_all_categories(self.apps)
            for cat in categories:
                if cat and cat != DEFAULT_CATEGORY:
                    self.category_combo.addItem(cat, cat)
            self.category_combo.currentIndexChanged.connect(self._on_category_changed)
            filter_row.addWidget(self.category_combo)
            filter_row.addStretch()

            count_lbl = QLabel()
            count_lbl.setStyleSheet("color: #7f8c8d; font-size: 12px;")
            self._count_label = count_lbl
            filter_row.addWidget(count_lbl)

            main_layout.addLayout(filter_row)

        self.grid_container = QWidget()
        self._grid_layout = QGridLayout(self.grid_container)
        self._grid_layout.setSpacing(24)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        main_layout.addWidget(self.grid_container, 1)

        self._render_apps()
        self._update_count()

    def _render_apps(self):
        for card in self._cards:
            self._grid_layout.removeWidget(card)
            card.setParent(None)
            card.deleteLater()
        self._cards = []

        if self._current_category == "all":
            filtered = self.apps
        else:
            filtered = [
                a for a in self.apps
                if a.get("category", DEFAULT_CATEGORY) == self._current_category
            ]

        n = len(filtered)
        if n <= 4:
            max_cols = 2
        elif n <= 9:
            max_cols = 3
        else:
            max_cols = 4

        row, col = 0, 0
        for idx, app in enumerate(filtered):
            card = AppCard(app)
            card.clicked.connect(lambda checked, c=card, a=app: self._launch(a, c))
            self._grid_layout.addWidget(card, row, col)
            self._cards.append(card)
            # Stagger fade-in
            QTimer.singleShot(
                idx * 60,
                lambda c=card: fade_in(c, duration="fast"),
            )

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def _on_category_changed(self, index: int):
        self._current_category = self.category_combo.itemData(index) or "all"
        self._render_apps()
        self._update_count()
        self.category_changed.emit(self._current_category)

    def _update_count(self):
        if hasattr(self, '_count_label'):
            visible = len(self._cards)
            total = len(self.apps)
            if self._current_category == "all":
                self._count_label.setText(f"{total} apps")
            else:
                self._count_label.setText(f"{visible} de {total} apps")

    def update_apps(self, apps: list):
        self.apps = apps
        if self._show_category_filter:
            current_text = self.category_combo.currentText()
            self.category_combo.blockSignals(True)
            self.category_combo.clear()
            self.category_combo.addItem("Todas las categorías", "all")
            categories = app_category_manager.get_all_categories(apps)
            for cat in categories:
                if cat and cat != DEFAULT_CATEGORY:
                    self.category_combo.addItem(cat, cat)
            idx = self.category_combo.findText(current_text)
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)
            self.category_combo.blockSignals(False)
        self._render_apps()
        self._update_count()

    def _launch(self, app_info, card):
        card.flash()
        error = launch_application(app_info)
        if error and self.on_launch:
            self.on_launch(error, app_info)
