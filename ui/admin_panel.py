import os
from datetime import datetime
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QListWidget, QListWidgetItem, QFileDialog,
                             QLineEdit, QFormLayout, QMessageBox, QCheckBox,
                             QTabWidget, QWidget, QFrame, QComboBox, QScrollArea,
                             QSpinBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl, QTimer
from PyQt6.QtGui import QDesktopServices, QFont

from core.logger import get_logger
from core.icon_utils import extract_and_save_icon
from core.calendar_manager import CalendarManager
from core.theme_manager import theme_manager, THEMES
from ui.theme_selector import ThemeSelectorDialog
from ui.admin_widgets.wallpaper_gallery import WallpaperGalleryDialog
from ui.admin_widgets.admin_preview import AdminPreviewFrame
from ui.admin_widgets.usage_dashboard import UsageDashboardWidget


logger = get_logger("ui.admin_panel")


ADMIN_TOUCH_QSS = """
QDialog {
    background-color: #1e2a38;
}

QDialog QLabel {
    color: #ecf0f1;
    background: transparent;
}

QDialog QLabel#SectionTitle {
    color: #3498db;
    font-size: 16px;
    font-weight: bold;
    margin-bottom: 6px;
}

QDialog QLabel#HelpText {
    color: #95a5a6;
    font-size: 12px;
    font-style: italic;
}

QTabWidget::pane {
    border: 1px solid #34495e;
    background: #1e2a38;
    border-radius: 8px;
}

QTabBar::tab {
    background: #2c3e50;
    color: #bdc3c7;
    padding: 12px 24px;
    border: 1px solid #34495e;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 4px;
    font-size: 13px;
    font-weight: 600;
    min-width: 110px;
}

QTabBar::tab:selected {
    background: #3498db;
    color: white;
}

QTabBar::tab:hover:!selected {
    background: #34495e;
    color: #ecf0f1;
}

QPushButton {
    background-color: #34495e;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 18px;
    font-size: 14px;
    font-weight: 600;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #3d566e;
}

QPushButton:pressed {
    background-color: #2c3e50;
}

QPushButton#PrimaryButton {
    background-color: #3498db;
    color: white;
}

QPushButton#PrimaryButton:hover {
    background-color: #2980b9;
}

QPushButton#PrimaryButton:pressed {
    background-color: #1f6391;
}

QPushButton#DangerButton {
    background-color: #e74c3c;
    color: white;
}

QPushButton#DangerButton:hover {
    background-color: #c0392b;
}

QPushButton#DangerButton:pressed {
    background-color: #a93226;
}

QPushButton#SuccessButton {
    background-color: #27ae60;
    color: white;
}

QPushButton#SuccessButton:hover {
    background-color: #229954;
}

QLineEdit {
    background-color: #2c3e50;
    color: #ecf0f1;
    border: 2px solid #34495e;
    border-radius: 6px;
    padding: 10px;
    font-size: 14px;
    selection-background-color: #3498db;
}

QLineEdit:focus {
    border-color: #3498db;
}

QSpinBox {
    background-color: #2c3e50;
    color: #ecf0f1;
    border: 2px solid #34495e;
    border-radius: 6px;
    padding: 6px 8px;
    font-size: 14px;
    min-height: 28px;
}

QSpinBox:focus {
    border-color: #3498db;
}

QCheckBox {
    color: #ecf0f1;
    font-size: 14px;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 22px;
    height: 22px;
    border: 2px solid #34495e;
    border-radius: 4px;
    background-color: #2c3e50;
}

QCheckBox::indicator:hover {
    border-color: #3498db;
}

QCheckBox::indicator:checked {
    background-color: #3498db;
    border-color: #3498db;
}

QListWidget {
    background-color: #2c3e50;
    color: #ecf0f1;
    border: 1px solid #34495e;
    border-radius: 6px;
    padding: 4px;
    font-size: 14px;
}

QListWidget::item {
    padding: 10px 8px;
    border-radius: 4px;
    margin: 2px 0;
}

QListWidget::item:selected {
    background-color: #3498db;
    color: white;
}

QListWidget::item:hover:!selected {
    background-color: #34495e;
}

QComboBox {
    background-color: #2c3e50;
    color: #ecf0f1;
    border: 2px solid #34495e;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 14px;
    min-height: 28px;
}

QComboBox:hover {
    border-color: #3498db;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox QAbstractItemView {
    background-color: #2c3e50;
    color: #ecf0f1;
    border: 1px solid #34495e;
    selection-background-color: #3498db;
}

QFrame#Section {
    background-color: #2c3e50;
    border-radius: 8px;
    padding: 12px;
}

QScrollBar:vertical {
    background: #1e2a38;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background: #34495e;
    border-radius: 6px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #3d566e;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
    height: 0;
}
"""


class CalendarAuthWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, manager, flow):
        super().__init__()
        self.manager = manager
        self.flow = flow

    def run(self):
        try:
            success = self.manager.complete_device_flow(self.flow)
            if success:
                self.finished.emit(True, "Conexión establecida con éxito.")
            else:
                self.finished.emit(False, "No se pudo completar la conexión.")
        except Exception as e:
            self.finished.emit(False, f"Error durante la conexión: {e}")


def make_section(title: str, parent_layout, help_text: str = "") -> QFrame:
    section = QFrame()
    section.setObjectName("Section")
    section_layout = QVBoxLayout(section)
    section_layout.setContentsMargins(14, 12, 14, 12)
    section_layout.setSpacing(8)

    title_label = QLabel(title)
    title_label.setObjectName("SectionTitle")
    section_layout.addWidget(title_label)

    if help_text:
        help_label = QLabel(help_text)
        help_label.setObjectName("HelpText")
        help_label.setWordWrap(True)
        section_layout.addWidget(help_label)

    parent_layout.addWidget(section)
    return section


def make_field(label_text: str, widget: QWidget) -> QHBoxLayout:
    row = QHBoxLayout()
    label = QLabel(label_text)
    label.setMinimumWidth(160)
    label.setStyleSheet("font-size: 14px;")
    row.addWidget(label)
    row.addWidget(widget, 1)
    return row


class AdminPanelDialog(QDialog):
    def __init__(self, config_manager, parent=None, calendar_manager=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.calendar_manager = calendar_manager
        self.setStyleSheet(ADMIN_TOUCH_QSS)
        self.init_ui()
        self._update_auth_status_label()
        self._start_preview_clock()

    def _start_preview_clock(self):
        self._preview_timer = QTimer(self)
        self._preview_timer.timeout.connect(lambda: self.preview.update_time() if hasattr(self, 'preview') else None)
        self._preview_timer.start(1000)

    def init_ui(self):
        self.setWindowTitle("Panel de Control — Administrador")
        self.resize(960, 720)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setStyleSheet(
            "QFrame { background-color: #2c3e50; padding: 16px; border-bottom: 2px solid #3498db; }"
        )
        header_layout = QHBoxLayout(header)
        title = QLabel("⚙ Panel de Administración")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        main_layout.addWidget(header)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabWidget { padding: 12px; background: #1e2a38; }")
        main_layout.addWidget(self.tabs, 1)

        # Preview
        self.preview = AdminPreviewFrame()
        self.preview.update_corporate_name(
            self.config_manager.config.get("corporate_name", "")
        )
        self.preview.update_time()

        self.apps_tab = QWidget()
        self.setup_apps_tab()
        self.tabs.addTab(self.apps_tab, "  📦 Aplicaciones  ")

        self.calendar_tab = QWidget()
        self.setup_calendar_tab()
        self.tabs.addTab(self.calendar_tab, "  📅 Calendario  ")

        self.theme_tab = QWidget()
        self.setup_theme_tab()
        self.tabs.addTab(self.theme_tab, "  🎨 Apariencia  ")

        self.general_tab = QWidget()
        self.setup_general_tab()
        self.tabs.addTab(self.general_tab, "  ⚙ General  ")

        self.audit_tab = QWidget()
        self.setup_audit_tab()
        self.tabs.addTab(self.audit_tab, "  📊 Auditoría  ")

        self.hdmi_tab = QWidget()
        self.setup_hdmi_tab()
        self.tabs.addTab(self.hdmi_tab, "  🖥️ Pantalla Externa  ")

        # Footer
        footer = QFrame()
        footer.setStyleSheet("QFrame { background-color: #2c3e50; padding: 12px; border-top: 1px solid #34495e; }")
        footer_layout = QHBoxLayout(footer)

        self.exit_app_btn = QPushButton("⏻ Cerrar Kiosco y Volver a Windows")
        self.exit_app_btn.setObjectName("DangerButton")
        self.exit_app_btn.setMinimumHeight(48)
        self.exit_app_btn.clicked.connect(self.exit_kiosk)
        footer_layout.addWidget(self.exit_app_btn)

        footer_layout.addStretch()

        self.close_btn = QPushButton("✓ Cerrar Panel")
        self.close_btn.setObjectName("PrimaryButton")
        self.close_btn.setMinimumHeight(48)
        self.close_btn.setMinimumWidth(160)
        self.close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(self.close_btn)

        main_layout.addWidget(footer)

    # ──────────────────────────────────────────────────────────────────
    #  TAB APLICACIONES
    # ──────────────────────────────────────────────────────────────────
    def setup_apps_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        section = make_section("Aplicaciones disponibles", layout, "Reordena con los botones. Selecciona una app para moverla o eliminarla.")

        section_layout = section.layout()

        list_row = QHBoxLayout()
        self.app_list = QListWidget()
        self.refresh_list()
        self.app_list.setMinimumHeight(220)
        list_row.addWidget(self.app_list, 1)

        order_col = QVBoxLayout()
        order_col.setSpacing(8)
        up_btn = QPushButton("▲ Subir")
        up_btn.setMinimumHeight(48)
        up_btn.setToolTip("Mover la app seleccionada hacia arriba")
        up_btn.clicked.connect(lambda: self._move_app(-1))

        down_btn = QPushButton("▼ Bajar")
        down_btn.setMinimumHeight(48)
        down_btn.setToolTip("Mover la app seleccionada hacia abajo")
        down_btn.clicked.connect(lambda: self._move_app(1))

        order_col.addWidget(up_btn)
        order_col.addWidget(down_btn)
        list_row.addLayout(order_col)
        section_layout.addLayout(list_row)

        self.remove_btn = QPushButton("🗑 Eliminar Aplicación Seleccionada")
        self.remove_btn.setObjectName("DangerButton")
        self.remove_btn.setMinimumHeight(48)
        self.remove_btn.clicked.connect(self.remove_selected_app)
        section_layout.addWidget(self.remove_btn)

        add_section = make_section("Añadir Nueva Aplicación", layout, "Indica un nombre y la ruta del ejecutable. Pulsa 'Examinar...' para buscarlo.")
        add_layout = add_section.layout()

        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre visible (ej: Microsoft Teams)")

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("C:\\Ruta\\al\\programa.exe")

        browse_btn = QPushButton("📁 Examinar...")
        browse_btn.setMinimumHeight(40)
        browse_btn.clicked.connect(self.browse_exe)

        path_layout = QHBoxLayout()
        path_layout.addWidget(self.path_input, 1)
        path_layout.addWidget(browse_btn)

        form_layout.addRow("Nombre:", self.name_input)
        form_layout.addRow("Ruta EXE:", path_layout)
        add_layout.addLayout(form_layout)

        add_btn = QPushButton("➕ Añadir Aplicación")
        add_btn.setObjectName("PrimaryButton")
        add_btn.setMinimumHeight(48)
        add_btn.clicked.connect(self.add_app)
        add_layout.addWidget(add_btn)

        layout.addStretch()
        scroll.setWidget(container)
        self.apps_tab.layout = QVBoxLayout(self.apps_tab)
        self.apps_tab.layout.setContentsMargins(0, 0, 0, 0)
        self.apps_tab.layout.addWidget(scroll)

    def _move_app(self, direction: int):
        current_row = self.app_list.currentRow()
        if current_row < 0:
            return
        self.config_manager.move_app(current_row, direction)
        self.refresh_list()
        new_row = current_row + direction
        apps_count = len(self.config_manager.get_apps())
        if 0 <= new_row < apps_count:
            self.app_list.setCurrentRow(new_row)

    # ──────────────────────────────────────────────────────────────────
    #  TAB TEMA / APARIENCIA
    # ──────────────────────────────────────────────────────────────────
    def setup_theme_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # Vista previa
        preview_section = make_section(
            "Vista Previa en Vivo",
            layout,
            "Así se verá la pantalla principal con la configuración actual.",
        )
        preview_section.layout().addWidget(self.preview)

        # Selector de tema
        theme_section = make_section(
            "Tema Visual",
            layout,
            "Cambia el tema de la aplicación. El cambio se aplica al guardar.",
        )
        theme_layout = theme_section.layout()

        row = QHBoxLayout()
        lbl = QLabel("Tema actual:")
        lbl.setStyleSheet("font-size: 14px; min-width: 120px;")
        row.addWidget(lbl)

        self.theme_combo = QComboBox()
        self.theme_combo.setMinimumHeight(44)
        available_themes = theme_manager.get_available_themes()
        for theme_id, label, _ in available_themes:
            self.theme_combo.addItem(label, theme_id)
        current = self.config_manager.get_theme()
        for i in range(self.theme_combo.count()):
            if self.theme_combo.itemData(i) == current:
                self.theme_combo.setCurrentIndex(i)
                break
        self.theme_combo.currentIndexChanged.connect(self._on_theme_combo_changed)
        if len(available_themes) <= 1:
            self.theme_combo.setEnabled(False)
        row.addWidget(self.theme_combo, 1)

        preview_btn = QPushButton("👁 Vista Previa...")
        preview_btn.setMinimumHeight(44)
        preview_btn.clicked.connect(self._open_theme_selector)
        if len(available_themes) <= 1:
            preview_btn.setEnabled(False)
        row.addWidget(preview_btn)

        theme_layout.addLayout(row)
        self.theme_status = QLabel("")
        self.theme_status.setStyleSheet("color: #95a5a6; font-size: 12px; font-style: italic;")
        self.theme_status.setWordWrap(True)
        theme_layout.addWidget(self.theme_status)
        self._update_theme_status(current)

        # Wallpapers
        wallpaper_section = make_section(
            "Fondos de Pantalla",
            layout,
            "Carpeta donde se encuentran los fondos del carrusel. Usa la galería para gestionarlos visualmente.",
        )
        wp_layout = wallpaper_section.layout()

        folder_row = QHBoxLayout()
        self.wallpaper_folder_input = QLineEdit()
        self.wallpaper_folder_input.setText(
            self.config_manager.config.get("wallpaper_folder", "assets/wallpapers")
        )
        self.wallpaper_folder_input.textChanged.connect(self._on_wallpaper_change)
        folder_row.addWidget(self.wallpaper_folder_input, 1)

        browse_w_btn = QPushButton("📁 Examinar...")
        browse_w_btn.setMinimumHeight(40)
        browse_w_btn.clicked.connect(self.browse_wallpaper_folder)
        folder_row.addWidget(browse_w_btn)

        gallery_btn = QPushButton("🖼 Abrir Galería")
        gallery_btn.setObjectName("PrimaryButton")
        gallery_btn.setMinimumHeight(40)
        gallery_btn.clicked.connect(self._open_wallpaper_gallery)
        folder_row.addWidget(gallery_btn)
        wp_layout.addLayout(folder_row)

        interval_row = QHBoxLayout()
        interval_lbl = QLabel("Intervalo (segundos):")
        interval_lbl.setStyleSheet("font-size: 14px; min-width: 160px;")
        interval_row.addWidget(interval_lbl)
        self.wallpaper_interval_input = QSpinBox()
        self.wallpaper_interval_input.setRange(5, 3600)
        self.wallpaper_interval_input.setValue(
            int(self.config_manager.config.get("wallpaper_interval_seconds", 60))
        )
        self.wallpaper_interval_input.setSuffix(" s")
        self.wallpaper_interval_input.setMinimumHeight(40)
        interval_row.addWidget(self.wallpaper_interval_input, 1)
        wp_layout.addLayout(interval_row)

        self.wp_count_label = QLabel("")
        self.wp_count_label.setStyleSheet("color: #95a5a6; font-size: 12px;")
        wp_layout.addWidget(self.wp_count_label)
        self._refresh_wp_count()

        save_theme_btn = QPushButton("💾 Guardar Apariencia")
        save_theme_btn.setObjectName("PrimaryButton")
        save_theme_btn.setMinimumHeight(48)
        save_theme_btn.clicked.connect(self.save_appearance_config)
        layout.addWidget(save_theme_btn)

        layout.addStretch()
        scroll.setWidget(container)
        self.theme_tab.layout = QVBoxLayout(self.theme_tab)
        self.theme_tab.layout.setContentsMargins(0, 0, 0, 0)
        self.theme_tab.layout.addWidget(scroll)

    def _on_wallpaper_change(self, _):
        self._refresh_wp_count()

    def _refresh_wp_count(self):
        folder = self.wallpaper_folder_input.text()
        if not os.path.exists(folder):
            self.wp_count_label.setText("⚠ La carpeta no existe")
            self.wp_count_label.setStyleSheet("color: #e67e22; font-size: 12px;")
            return
        try:
            files = [
                f for f in os.listdir(folder)
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp'))
            ]
            self.wp_count_label.setText(f"✓ {len(files)} fondo(s) disponible(s)")
            self.wp_count_label.setStyleSheet("color: #27ae60; font-size: 12px;")
        except Exception as exc:
            logger.warning("Error contando wallpapers: %s", exc)
            self.wp_count_label.setText(f"Error: {exc}")

    def _on_theme_combo_changed(self, index: int):
        theme_id = self.theme_combo.itemData(index)
        if theme_id:
            self._apply_theme_live(theme_id)

    def _open_theme_selector(self):
        current = self.config_manager.get_theme()
        dlg = ThemeSelectorDialog(current, self)
        dlg.theme_selected.connect(self._on_theme_card_selected)
        if dlg.exec():
            theme_id = dlg.get_selected_theme()
            for i in range(self.theme_combo.count()):
                if self.theme_combo.itemData(i) == theme_id:
                    self.theme_combo.setCurrentIndex(i)
                    break

    def _on_theme_card_selected(self, theme_id: str):
        self._apply_theme_live(theme_id)
        for i in range(self.theme_combo.count()):
            if self.theme_combo.itemData(i) == theme_id:
                self.theme_combo.setCurrentIndex(i)
                break

    def _apply_theme_live(self, theme_id: str):
        from PyQt6.QtWidgets import QApplication
        qss = theme_manager.load_stylesheet(theme_id)
        QApplication.instance().setStyleSheet(qss)
        # El panel admin usa su propio QSS encima del tema,
        # pero refrescamos el label de estado.
        self._update_theme_status(theme_id)
        logger.info("Tema aplicado en vivo: %s", theme_id)

    def _update_theme_status(self, theme_id: str):
        label = THEMES.get(theme_id, {}).get("label", theme_id)
        self.theme_status.setText(
            f"✓ Tema actual: {label}. Pulsa 'Guardar Apariencia' para persistir el cambio."
        )

    def _open_wallpaper_gallery(self):
        folder = self.wallpaper_folder_input.text()
        dlg = WallpaperGalleryDialog(folder, self)
        if dlg.exec():
            selected = dlg.get_selected_file()
            if selected:
                self.wallpaper_folder_input.setText(os.path.dirname(selected))
                self._refresh_wp_count()

    def save_appearance_config(self):
        try:
            theme_id = self.theme_combo.currentData()
            self.config_manager.set_theme(theme_id)
            theme_manager.set_theme(theme_id)
            from PyQt6.QtWidgets import QApplication
            qss = theme_manager.load_stylesheet(theme_id)
            QApplication.instance().setStyleSheet(qss)

            self.config_manager.config["wallpaper_folder"] = self.wallpaper_folder_input.text()
            self.config_manager.config["wallpaper_interval_seconds"] = int(self.wallpaper_interval_input.value())
            self.config_manager.save_config()

            QMessageBox.information(
                self, "Apariencia Guardada",
                "Los cambios de apariencia se han guardado y aplicado.",
            )
        except Exception as exc:
            logger.error("Error guardando apariencia: %s", exc)
            QMessageBox.warning(self, "Error", f"No se pudo guardar: {exc}")

    # ──────────────────────────────────────────────────────────────────
    #  TAB GENERAL
    # ──────────────────────────────────────────────────────────────────
    def setup_general_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # Nombre corporativo
        corp_section = make_section("Identidad Corporativa", layout)
        corp_layout = corp_section.layout()

        self.corp_name_input = QLineEdit()
        self.corp_name_input.setText(self.config_manager.config.get("corporate_name", ""))
        self.corp_name_input.setMinimumHeight(44)
        self.corp_name_input.textChanged.connect(
            lambda t: self.preview.update_corporate_name(t)
        )
        corp_layout.addLayout(make_field("Nombre Corporativo:", self.corp_name_input))

        # Comportamiento
        inact_section = make_section("Comportamiento", layout, "Ajustes de alertas de reunión.")
        inact_layout = inact_section.layout()

        self.alert_minutes_input = QSpinBox()
        self.alert_minutes_input.setRange(1, 30)
        self.alert_minutes_input.setValue(
            int(self.config_manager.config.get("alert_minutes_before_meeting", 5))
        )
        self.alert_minutes_input.setSuffix(" min")
        self.alert_minutes_input.setMinimumHeight(44)
        inact_layout.addLayout(make_field("Alerta antes de reunión:", self.alert_minutes_input))

        # Notificaciones
        notif_section = make_section("Notificaciones", layout)
        notif_layout = notif_section.layout()

        self.sound_enabled_cb = QCheckBox("Activar sonido en alertas")
        self.sound_enabled_cb.setChecked(
            self.config_manager.config.get("notification_sound_enabled", True)
        )
        notif_layout.addWidget(self.sound_enabled_cb)

        sound_row = QHBoxLayout()
        self.sound_path_input = QLineEdit()
        self.sound_path_input.setText(
            self.config_manager.config.get("notification_sound_path", "")
        )
        self.sound_path_input.setPlaceholderText("(usar sonido por defecto)")
        self.sound_path_input.setMinimumHeight(40)
        sound_row.addWidget(self.sound_path_input, 1)

        browse_sound_btn = QPushButton("📁 Examinar...")
        browse_sound_btn.setMinimumHeight(40)
        browse_sound_btn.clicked.connect(self.browse_sound_file)
        sound_row.addWidget(browse_sound_btn)

        notif_layout.addLayout(make_field("Sonido personalizado:", self.sound_path_input))

        save_btn = QPushButton("💾 Guardar Configuración General")
        save_btn.setObjectName("PrimaryButton")
        save_btn.setMinimumHeight(48)
        save_btn.clicked.connect(self.save_general_config)
        layout.addWidget(save_btn)

        layout.addStretch()
        scroll.setWidget(container)
        self.general_tab.layout = QVBoxLayout(self.general_tab)
        self.general_tab.layout.setContentsMargins(0, 0, 0, 0)
        self.general_tab.layout.addWidget(scroll)

    def browse_sound_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar sonido", "",
            "Audio (*.wav *.mp3 *.ogg *.flac)"
        )
        if file_path:
            self.sound_path_input.setText(file_path.replace("/", "\\"))

    def save_general_config(self):
        try:
            self.config_manager.config["corporate_name"] = self.corp_name_input.text()
            self.config_manager.config["alert_minutes_before_meeting"] = int(self.alert_minutes_input.value())
            self.config_manager.config["notification_sound_enabled"] = self.sound_enabled_cb.isChecked()
            self.config_manager.config["notification_sound_path"] = self.sound_path_input.text()

            self.config_manager.save_config()

            QMessageBox.information(
                self, "Configuración Guardada",
                "Los cambios generales se han guardado.\n"
                "Algunos cambios pueden requerir reiniciar la aplicación.",
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Error", f"Valor inválido: {exc}")
        except Exception as exc:
            logger.error("Error guardando config general: %s", exc)
            QMessageBox.warning(self, "Error", f"No se pudo guardar: {exc}")

    def browse_wallpaper_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Seleccionar Carpeta de Fondos",
            self.wallpaper_folder_input.text(),
        )
        if folder:
            self.wallpaper_folder_input.setText(folder.replace("/", "\\"))

    # ──────────────────────────────────────────────────────────────────
    #  TAB HDMI / PANTALLA EXTERNA
    # ──────────────────────────────────────────────────────────────────
    def setup_hdmi_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # Estado del módulo
        status_section = make_section(
            "Estado del módulo",
            layout,
            "Comprueba si se detecta algún dispositivo de captura HDMI en Windows.",
        )
        status_layout = status_section.layout()

        self.hdmi_status_label = QLabel("")
        self.hdmi_status_label.setWordWrap(True)
        self.hdmi_status_label.setStyleSheet("font-size: 14px;")
        status_layout.addWidget(self.hdmi_status_label)

        refresh_btn = QPushButton("🔄 Refrescar lista de dispositivos")
        refresh_btn.setMinimumHeight(40)
        refresh_btn.clicked.connect(self._refresh_hdmi_devices)
        status_layout.addWidget(refresh_btn)

        # Configuración
        config_section = make_section(
            "Configuración de captura",
            layout,
            "Selecciona el dispositivo de captura HDMI y sus parámetros.",
        )
        config_layout = config_section.layout()

        self.hdmi_enabled_cb = QCheckBox("Habilitar botón 'Compartir pantalla' en la app")
        current_hdmi = self.config_manager.get_hdmi_input()
        self.hdmi_enabled_cb.setChecked(current_hdmi["enabled"])
        config_layout.addWidget(self.hdmi_enabled_cb)

        # Dispositivo
        dev_row = QHBoxLayout()
        dev_lbl = QLabel("Dispositivo:")
        dev_lbl.setMinimumWidth(160)
        dev_lbl.setStyleSheet("font-size: 14px;")
        dev_row.addWidget(dev_lbl)
        self.hdmi_device_combo = QComboBox()
        self.hdmi_device_combo.setMinimumHeight(40)
        self.hdmi_device_combo.setMinimumWidth(280)
        dev_row.addWidget(self.hdmi_device_combo, 1)
        config_layout.addLayout(dev_row)

        # Resolución
        res_row = QHBoxLayout()
        res_lbl = QLabel("Resolución:")
        res_lbl.setMinimumWidth(160)
        res_lbl.setStyleSheet("font-size: 14px;")
        res_row.addWidget(res_lbl)
        self.hdmi_resolution_combo = QComboBox()
        self.hdmi_resolution_combo.setMinimumHeight(40)
        self.hdmi_resolution_combo.addItem("1920 × 1080 (Full HD)", (1920, 1080))
        self.hdmi_resolution_combo.addItem("1280 × 720 (HD)", (1280, 720))
        self.hdmi_resolution_combo.addItem("640 × 480 (VGA)", (640, 480))
        # Seleccionar la resolución actual
        current_res = (current_hdmi["width"], current_hdmi["height"])
        for i in range(self.hdmi_resolution_combo.count()):
            if self.hdmi_resolution_combo.itemData(i) == current_res:
                self.hdmi_resolution_combo.setCurrentIndex(i)
                break
        res_row.addWidget(self.hdmi_resolution_combo, 1)
        config_layout.addLayout(res_row)

        # FPS
        fps_row = QHBoxLayout()
        fps_lbl = QLabel("FPS:")
        fps_lbl.setMinimumWidth(160)
        fps_lbl.setStyleSheet("font-size: 14px;")
        fps_row.addWidget(fps_lbl)
        self.hdmi_fps_combo = QComboBox()
        self.hdmi_fps_combo.setMinimumHeight(40)
        self.hdmi_fps_combo.addItem("15 fps", 15)
        self.hdmi_fps_combo.addItem("30 fps (recomendado)", 30)
        self.hdmi_fps_combo.addItem("60 fps", 60)
        for i in range(self.hdmi_fps_combo.count()):
            if self.hdmi_fps_combo.itemData(i) == current_hdmi["fps"]:
                self.hdmi_fps_combo.setCurrentIndex(i)
                break
        fps_row.addWidget(self.hdmi_fps_combo, 1)
        config_layout.addLayout(fps_row)

        # Botones
        btn_row = QHBoxLayout()
        test_btn = QPushButton("🔍 Probar 5 segundos")
        test_btn.setMinimumHeight(44)
        test_btn.clicked.connect(self._test_hdmi_5s)
        btn_row.addWidget(test_btn)

        save_btn = QPushButton("💾 Guardar Configuración")
        save_btn.setObjectName("PrimaryButton")
        save_btn.setMinimumHeight(44)
        save_btn.clicked.connect(self._save_hdmi_config)
        btn_row.addWidget(save_btn)

        config_layout.addLayout(btn_row)

        # Información de ayuda
        help_section = make_section(
            "Información",
            layout,
            "Cómo funciona:\n\n"
            "• La pantalla interactiva expone su puerto HDMI de entrada como un "
            "dispositivo de captura DirectShow en Windows.\n"
            "• Al pulsar 'Compartir pantalla' en la app principal, se abre una "
            "ventana flotante con el video en vivo del dispositivo.\n"
            "• Para que aparezca el botón en el grid de apps, el módulo debe "
            "estar habilitado aquí.\n"
            "• La ventana se cierra con la X como cualquier aplicación.",
        )
        help_layout = help_section.layout()
        help_label = QLabel(
            "Si no aparece ningún dispositivo:\n"
            "1. Verifica que el driver de captura está instalado\n"
            "2. Comprueba en Administrador de dispositivos de Windows\n"
            "3. Si la pantalla usa HDMI-in como monitor secundario, necesitas "
            "una tarjeta capturadora USB externa"
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #95a5a6; font-size: 13px; line-height: 1.5;")
        help_layout.addWidget(help_label)

        layout.addStretch()
        scroll.setWidget(container)
        self.hdmi_tab.layout = QVBoxLayout(self.hdmi_tab)
        self.hdmi_tab.layout.setContentsMargins(0, 0, 0, 0)
        self.hdmi_tab.layout.addWidget(scroll)

        # Cargar dispositivos al iniciar
        self._refresh_hdmi_devices()

    def _refresh_hdmi_devices(self):
        """Enumera dispositivos y actualiza combo + label de estado."""
        try:
            from core.hdmi_capture import HDMICaptureManager

            if not HDMICaptureManager.is_available():
                self.hdmi_status_label.setText("✕ OpenCV no está instalado")
                self.hdmi_status_label.setStyleSheet(
                    "color: #e74c3c; font-size: 14px; font-weight: bold;"
                )
                self.hdmi_device_combo.clear()
                return

            devices = HDMICaptureManager.list_devices()
            current_hdmi = self.config_manager.get_hdmi_input()
            self.hdmi_device_combo.clear()

            if not devices:
                self.hdmi_status_label.setText(
                    "🟡 No se detectaron dispositivos de captura.\n"
                    "Verifica que el driver esté instalado y pulsa 'Refrescar'."
                )
                self.hdmi_status_label.setStyleSheet(
                    "color: #f39c12; font-size: 14px; font-weight: bold;"
                )
            else:
                for dev in devices:
                    self.hdmi_device_combo.addItem(dev["name"], dev["index"])
                # Seleccionar el actual
                for i in range(self.hdmi_device_combo.count()):
                    if self.hdmi_device_combo.itemData(i) == current_hdmi["device_index"]:
                        self.hdmi_device_combo.setCurrentIndex(i)
                        break

                self.hdmi_status_label.setText(
                    f"🟢 {len(devices)} dispositivo(s) detectado(s)"
                )
                self.hdmi_status_label.setStyleSheet(
                    "color: #27ae60; font-size: 14px; font-weight: bold;"
                )

        except Exception as exc:
            logger.error("Error refrescando dispositivos HDMI: %s", exc)
            self.hdmi_status_label.setText(f"✕ Error: {exc}")
            self.hdmi_status_label.setStyleSheet(
                "color: #e74c3c; font-size: 14px;"
            )

    def _save_hdmi_config(self):
        try:
            device_index = self.hdmi_device_combo.currentData()
            if device_index is None:
                QMessageBox.warning(
                    self, "Sin dispositivo",
                    "No hay ningún dispositivo seleccionado.\n"
                    "Pulsa 'Refrescar lista de dispositivos' primero."
                )
                return

            w, h = self.hdmi_resolution_combo.currentData()
            fps = self.hdmi_fps_combo.currentData()

            self.config_manager.set_hdmi_input(
                enabled=self.hdmi_enabled_cb.isChecked(),
                device_index=int(device_index),
                width=int(w),
                height=int(h),
                fps=int(fps),
            )
            QMessageBox.information(
                self, "Configuración guardada",
                "La configuración de 'Compartir pantalla' se ha guardado.\n"
                "El botón aparecerá en el grid de apps al regresar a la pantalla principal."
            )
        except Exception as exc:
            logger.error("Error guardando config HDMI: %s", exc)
            QMessageBox.warning(self, "Error", f"No se pudo guardar: {exc}")

    def _test_hdmi_5s(self):
        """Abre una ventana de prueba con el viewer durante 5 segundos."""
        from ui.hdmi_viewer_window import HDMIViewerWindow
        from PyQt6.QtCore import QTimer

        if not self.hdmi_device_combo.count():
            QMessageBox.warning(
                self, "Sin dispositivo",
                "No hay dispositivos detectados para probar."
            )
            return

        device_index = self.hdmi_device_combo.currentData()
        w, h = self.hdmi_resolution_combo.currentData()
        fps = self.hdmi_fps_combo.currentData()

        try:
            test_window = HDMIViewerWindow(
                device_index=int(device_index),
                width=int(w),
                height=int(h),
                fps=int(fps),
                parent=None,
            )
            test_window.setWindowTitle("PRUEBA — Compartir Pantalla (5s)")
            test_window.show()

            def close_test():
                if test_window is not None:
                    try:
                        test_window.force_stop()
                    except Exception:
                        pass

            QTimer.singleShot(5000, close_test)
        except Exception as exc:
            logger.error("Error en test HDMI: %s", exc)
            QMessageBox.warning(self, "Error", f"No se pudo iniciar prueba: {exc}")

    # ──────────────────────────────────────────────────────────────────
    #  TAB CALENDARIO M365
    # ──────────────────────────────────────────────────────────────────
    def setup_calendar_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # Estado
        status_section = make_section("Estado de la cuenta", layout)
        status_layout = status_section.layout()

        self.auth_status_label = QLabel("Estado: —")
        self.auth_status_label.setWordWrap(True)
        self.auth_status_label.setStyleSheet("font-size: 14px;")
        status_layout.addWidget(self.auth_status_label)

        self.unlink_btn = QPushButton("🔓 Desvincular Cuenta")
        self.unlink_btn.setObjectName("DangerButton")
        self.unlink_btn.setMinimumHeight(44)
        self.unlink_btn.clicked.connect(self.logout_calendar)
        self.unlink_btn.hide()
        status_layout.addWidget(self.unlink_btn)

        # Habilitar
        enable_section = make_section("Configuración de Microsoft 365", layout)
        enable_layout = enable_section.layout()

        self.cal_enabled_cb = QCheckBox("Habilitar calendario en la pantalla principal")
        self.cal_enabled_cb.setChecked(self.config_manager.config.get("calendar_enabled", False))
        enable_layout.addWidget(self.cal_enabled_cb)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.client_id_input = QLineEdit()
        self.client_id_input.setText(self.config_manager.get_client_id())
        self.client_id_input.setPlaceholderText("Client ID de Azure AD")

        self.client_secret_input = QLineEdit()
        self.client_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.client_secret_input.setText(self.config_manager.get_client_secret())
        self.client_secret_input.setPlaceholderText("Client Secret (opcional, recomendado para salas)")

        self.tenant_id_input = QLineEdit()
        self.tenant_id_input.setText(self.config_manager.get_tenant_id())
        self.tenant_id_input.setPlaceholderText("Tenant ID o 'common'")

        self.room_email_input = QLineEdit()
        self.room_email_input.setText(self.config_manager.get_room_email())
        self.room_email_input.setPlaceholderText("sala.reuniones@empresa.com  (vacío = calendario del usuario)")

        form_layout.addRow("Client ID:", self.client_id_input)
        form_layout.addRow("Client Secret:", self.client_secret_input)
        form_layout.addRow("Tenant ID:", self.tenant_id_input)
        form_layout.addRow("Email de sala:", self.room_email_input)
        enable_layout.addLayout(form_layout)

        save_cal_btn = QPushButton("💾 Guardar Configuración")
        save_cal_btn.setObjectName("PrimaryButton")
        save_cal_btn.setMinimumHeight(48)
        save_cal_btn.clicked.connect(self.save_calendar_config)
        enable_layout.addWidget(save_cal_btn)

        # Vinculación
        link_section = make_section("Vinculación de Cuenta", layout, "Para modo usuario (sin Client Secret). Se abrirá Microsoft en el navegador.")
        link_layout = link_section.layout()

        self.link_btn = QPushButton("🔗 Iniciar Vinculación (Device Login)")
        self.link_btn.setObjectName("PrimaryButton")
        self.link_btn.setMinimumHeight(48)
        self.link_btn.clicked.connect(self.start_calendar_auth)
        link_layout.addWidget(self.link_btn)

        layout.addStretch()
        scroll.setWidget(container)
        self.calendar_tab.layout = QVBoxLayout(self.calendar_tab)
        self.calendar_tab.layout.setContentsMargins(0, 0, 0, 0)
        self.calendar_tab.layout.addWidget(scroll)

    def logout_calendar(self):
        if self.calendar_manager:
            self.calendar_manager.logout()
            self._update_auth_status_label()
            QMessageBox.information(self, "Cuenta Desvinculada", "Se ha cerrado la sesión del calendario.")

    def _update_auth_status_label(self):
        if not hasattr(self, 'auth_status_label'):
            return

        if self.calendar_manager is None:
            self.auth_status_label.setText("Estado: No configurado")
            self.auth_status_label.setStyleSheet("color: #95a5a6; font-size: 14px;")
            self.unlink_btn.hide()
            return

        status = self.calendar_manager.auth_status
        accounts = self.calendar_manager.app.get_accounts()

        if status == "ok" and accounts:
            user = accounts[0].get("username", "cuenta vinculada")
            self.auth_status_label.setText(f"✓ Vinculado como: {user}")
            self.auth_status_label.setStyleSheet("color: #27ae60; font-size: 14px; font-weight: bold;")
            self.unlink_btn.show()
        elif status == "forbidden":
            self.auth_status_label.setText("✕ Error 403 (Prohibido) — Revisa permisos Azure o email de sala.")
            self.auth_status_label.setStyleSheet("color: #e74c3c; font-size: 14px; font-weight: bold;")
            self.unlink_btn.show()
        elif status == "expired":
            self.auth_status_label.setText("⚠ Sesión caducada — Vuelve a vincular.")
            self.auth_status_label.setStyleSheet("color: #f39c12; font-size: 14px; font-weight: bold;")
            self.unlink_btn.show()
        elif accounts:
            user = accounts[0].get("username", "cuenta vinculada")
            self.auth_status_label.setText(f"⚠ Vinculado ({user}) pero con problemas de conexión.")
            self.auth_status_label.setStyleSheet("color: #f39c12; font-size: 14px;")
            self.unlink_btn.show()
        else:
            self.auth_status_label.setText("Estado: No vinculado")
            self.auth_status_label.setStyleSheet("color: #95a5a6; font-size: 14px;")
            self.unlink_btn.hide()

    def save_calendar_config(self):
        self.config_manager.config["calendar_enabled"] = self.cal_enabled_cb.isChecked()
        self.config_manager.config["client_id"] = self.client_id_input.text().strip()
        self.config_manager.config["client_secret"] = self.client_secret_input.text().strip()
        self.config_manager.config["tenant_id"] = self.tenant_id_input.text().strip()
        self.config_manager.config["room_email"] = self.room_email_input.text().strip()
        self.config_manager.save_config()

        if self.config_manager.config["client_secret"]:
            self.calendar_manager = CalendarManager(
                self.config_manager.config["client_id"],
                self.config_manager.config["tenant_id"],
                self.config_manager.config["room_email"],
                self.config_manager.config["client_secret"]
            )
            self._update_auth_status_label()

        QMessageBox.information(
            self, "Configuración Guardada",
            "Los cambios en el calendario se han guardado.",
        )

    def start_calendar_auth(self):
        client_id = self.client_id_input.text().strip()
        tenant_id = self.tenant_id_input.text().strip() or "common"
        client_secret = self.client_secret_input.text().strip()

        if not client_id:
            QMessageBox.warning(self, "Error", "Debes introducir un Client ID válido.")
            return

        if client_secret:
            self.calendar_manager = CalendarManager(
                client_id, tenant_id,
                self.room_email_input.text().strip(), client_secret
            )
            self._update_auth_status_label()
            QMessageBox.information(
                self, "Modo Aplicación",
                "Se está usando Client Secret. No es necesario vincular manualmente.",
            )
            return

        try:
            if (self.calendar_manager is None
                or self.calendar_manager.client_secret is not None
                or self.calendar_manager.client_id != client_id):
                self.calendar_manager = CalendarManager(client_id, tenant_id)

            flow = self.calendar_manager.initiate_device_flow()
            if not flow:
                raise Exception("El flujo de dispositivo no está disponible.")

            QDesktopServices.openUrl(QUrl(flow['verification_uri']))

            self.auth_status_label.setText(
                f"🔐 CÓDIGO: {flow['user_code']} — "
                f"Ve a {flow['verification_uri']}"
            )
            self.auth_status_label.setStyleSheet(
                "color: #f39c12; font-size: 14px; font-weight: bold;"
            )

            self.link_btn.setEnabled(False)
            self.link_btn.setText("⏳ Esperando en Microsoft...")

            self.auth_worker = CalendarAuthWorker(self.calendar_manager, flow)
            self.auth_worker.finished.connect(self.on_auth_finished)
            self.auth_worker.start()

        except Exception as e:
            logger.error("Error en device flow: %s", e, exc_info=True)
            QMessageBox.critical(
                self, "Error de Autenticación",
                f"No se pudo iniciar el proceso.\n\nDetalle: {str(e)}",
            )

    def on_auth_finished(self, success, message):
        self.link_btn.setEnabled(True)
        self.link_btn.setText("🔗 Iniciar Vinculación (Device Login)")

        if success:
            self._update_auth_status_label()
            QMessageBox.information(self, "Éxito", message)
        else:
            self.auth_status_label.setText("✕ Fallo en la vinculación")
            self.auth_status_label.setStyleSheet("color: #e74c3c; font-size: 14px; font-weight: bold;")
            QMessageBox.warning(self, "Error", message)

    # ──────────────────────────────────────────────────────────────────
    #  TAB AUDITORÍA
    # ──────────────────────────────────────────────────────────────────
    def setup_audit_tab(self):
        layout = QVBoxLayout(self.audit_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.dashboard = UsageDashboardWidget()
        layout.addWidget(self.dashboard)

    # ──────────────────────────────────────────────────────────────────
    #  Helpers
    # ──────────────────────────────────────────────────────────────────
    def refresh_list(self):
        self.app_list.clear()
        for app in self.config_manager.get_apps():
            item = QListWidgetItem(f"  {app['name']}")
            item.setToolTip(app.get('path', ''))
            self.app_list.addItem(item)

    def browse_exe(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Ejecutable", "C:\\Program Files",
            "Executables (*.exe)"
        )
        if file_path:
            clean_path = file_path.replace("/", "\\")
            self.path_input.setText(clean_path)
            if not self.name_input.text():
                name = os.path.splitext(os.path.basename(clean_path))[0]
                self.name_input.setText(name)

    def add_app(self):
        name = self.name_input.text().strip()
        path = self.path_input.text().strip()
        if name and path:
            icon_path = extract_and_save_icon(path)
            self.config_manager.add_app(name, path, icon_path)
            self.refresh_list()
            self.name_input.clear()
            self.path_input.clear()
            QMessageBox.information(self, "Éxito", f"Aplicación '{name}' añadida con éxito.")
        else:
            QMessageBox.warning(self, "Error", "Debes completar nombre y ruta")

    def remove_selected_app(self):
        current_row = self.app_list.currentRow()
        if current_row >= 0:
            app_name = self.app_list.item(current_row).text().strip()
            reply = QMessageBox.question(
                self, "Confirmar eliminación",
                f"¿Eliminar '{app_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.config_manager.remove_app(current_row)
                self.refresh_list()
        else:
            QMessageBox.warning(self, "Error", "Selecciona una aplicación para eliminar")

    def exit_kiosk(self):
        reply = QMessageBox.question(
            self, "Confirmar",
            "¿Estás seguro de que quieres salir del sistema de kiosco?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            from core import audit
            audit.log_kiosk_exit()
            from PyQt6.QtWidgets import QApplication
            QApplication.quit()
