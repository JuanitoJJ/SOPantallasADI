import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QWidget, QFileDialog, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont

from core.logger import get_logger


logger = get_logger("ui.admin_widgets.wallpaper_gallery")


SUPPORTED_EXTS = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')


class WallpaperThumb(QFrame):
    selected = pyqtSignal(str)
    deleted = pyqtSignal(str)

    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setObjectName("WallpaperThumb")
        self.setFixedSize(220, 150)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet(
            "background-color: #2c3e50; border-radius: 6px;"
        )
        self._load_image()
        layout.addWidget(self.image_label, 1)

        footer = QHBoxLayout()
        name = QLabel(os.path.basename(file_path))
        name.setStyleSheet("color: #bdc3c7; font-size: 10px;")
        name.setMaximumWidth(140)
        name.setToolTip(file_path)
        footer.addWidget(name, 1)

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(20, 20)
        del_btn.setStyleSheet(
            "QPushButton { background-color: #e74c3c; color: white; "
            "border: none; border-radius: 10px; font-weight: bold; "
            "font-size: 10px; }"
            "QPushButton:hover { background-color: #c0392b; }"
        )
        del_btn.clicked.connect(lambda: self.deleted.emit(self.file_path))
        footer.addWidget(del_btn, 0)

        layout.addLayout(footer)

    def _load_image(self):
        try:
            pix = QPixmap(self.file_path)
            if pix.isNull():
                self.image_label.setText("Sin preview")
                return
            scaled = pix.scaled(
                210, 110,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.image_label.setPixmap(scaled)
        except Exception as exc:
            logger.warning("Error cargando preview de %s: %s", self.file_path, exc)
            self.image_label.setText("Error")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.selected.emit(self.file_path)
        super().mousePressEvent(event)

    def set_selected(self, selected: bool):
        border = "3px solid #3498db" if selected else "2px solid transparent"
        self.setStyleSheet(
            f"QFrame#WallpaperThumb {{ border: {border}; border-radius: 6px; }}"
        )


class WallpaperGalleryDialog(QDialog):
    def __init__(self, folder: str, parent=None):
        super().__init__(parent)
        self.folder = folder
        self.selected_file = ""
        self._thumbs = []
        self._init_ui()
        self._load_thumbs()

    def _init_ui(self):
        self.setWindowTitle("Galería de Fondos de Pantalla")
        self.setMinimumSize(900, 600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setStyleSheet("background-color: #2c3e50;")
        header.setMinimumHeight(60)
        header_layout = QHBoxLayout(header)

        title = QLabel(f"Fondos en: {self.folder}")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: white;")
        header_layout.addWidget(title, 1)

        self.count_label = QLabel("0 fondos")
        self.count_label.setStyleSheet("color: #bdc3c7;")
        header_layout.addWidget(self.count_label)

        layout.addWidget(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(
            "QScrollArea { background-color: #1a1a1a; border: none; }"
        )
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background-color: #1a1a1a;")
        self.scroll_grid = QGridLayout(self.scroll_content)
        self.scroll_grid.setContentsMargins(15, 15, 15, 15)
        self.scroll_grid.setSpacing(12)
        self.scroll_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll, 1)

        footer = QFrame()
        footer.setStyleSheet("background-color: #2c3e50; padding: 10px;")
        footer_layout = QHBoxLayout(footer)

        refresh_btn = QPushButton("🔄 Recargar")
        refresh_btn.setMinimumHeight(40)
        refresh_btn.setStyleSheet(
            "QPushButton { background-color: #34495e; color: white; "
            "border: none; border-radius: 6px; padding: 8px 16px; }"
            "QPushButton:hover { background-color: #2c3e50; }"
        )
        refresh_btn.clicked.connect(self._load_thumbs)
        footer_layout.addWidget(refresh_btn)

        add_btn = QPushButton("➕ Añadir fondos...")
        add_btn.setMinimumHeight(40)
        add_btn.setStyleSheet(
            "QPushButton { background-color: #3498db; color: white; "
            "border: none; border-radius: 6px; padding: 8px 16px; }"
            "QPushButton:hover { background-color: #2980b9; }"
        )
        add_btn.clicked.connect(self._add_files)
        footer_layout.addWidget(add_btn)

        footer_layout.addStretch()

        self.selection_label = QLabel("Seleccionado: —")
        self.selection_label.setStyleSheet("color: #bdc3c7;")
        footer_layout.addWidget(self.selection_label)

        select_btn = QPushButton("Establecer como inicial")
        select_btn.setMinimumHeight(40)
        select_btn.setStyleSheet(
            "QPushButton { background-color: #27ae60; color: white; "
            "border: none; border-radius: 6px; padding: 8px 16px; }"
            "QPushButton:hover { background-color: #229954; }"
        )
        select_btn.clicked.connect(self._on_select_clicked)
        footer_layout.addWidget(select_btn)

        close_btn = QPushButton("Cerrar")
        close_btn.setMinimumHeight(40)
        close_btn.clicked.connect(self.reject)
        footer_layout.addWidget(close_btn)

        layout.addWidget(footer)

    def _load_thumbs(self):
        while self.scroll_grid.count():
            item = self.scroll_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._thumbs.clear()

        if not os.path.exists(self.folder):
            self.count_label.setText("0 fondos (carpeta no existe)")
            return

        files = sorted([
            os.path.join(self.folder, f)
            for f in os.listdir(self.folder)
            if f.lower().endswith(SUPPORTED_EXTS)
        ])

        cols = 4
        for idx, file_path in enumerate(files):
            thumb = WallpaperThumb(file_path)
            thumb.selected.connect(self._on_thumb_selected)
            thumb.deleted.connect(self._on_thumb_deleted)
            self._thumbs.append(thumb)
            self.scroll_grid.addWidget(thumb, idx // cols, idx % cols)

        self.count_label.setText(f"{len(files)} fondo(s)")

    def _on_thumb_selected(self, file_path: str):
        self.selected_file = file_path
        self.selection_label.setText(f"Seleccionado: {os.path.basename(file_path)}")
        for thumb in self._thumbs:
            thumb.set_selected(thumb.file_path == file_path)

    def _on_thumb_deleted(self, file_path: str):
        try:
            os.remove(file_path)
            logger.info("Fondo eliminado: %s", file_path)
            self._load_thumbs()
        except Exception as exc:
            logger.error("No se pudo eliminar fondo: %s", exc)

    def _add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Seleccionar Fondos de Pantalla",
            self.folder,
            "Imágenes (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if not files:
            return
        import shutil
        added = 0
        for f in files:
            try:
                dest = os.path.join(self.folder, os.path.basename(f))
                if not os.path.exists(dest):
                    shutil.copy2(f, dest)
                    added += 1
            except Exception as exc:
                logger.warning("No se pudo copiar fondo: %s", exc)
        if added:
            logger.info("Añadidos %d fondos", added)
        self._load_thumbs()

    def _on_select_clicked(self):
        if self.selected_file:
            self.accept()
        else:
            self.selection_label.setText("Selecciona un fondo primero")

    def get_selected_file(self) -> str:
        return self.selected_file
