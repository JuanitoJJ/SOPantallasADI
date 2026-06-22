import os
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout,
    QPushButton, QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QSpinBox, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from core.logger import get_logger
from core import audit


logger = get_logger("ui.admin_widgets.dashboard")


class StatCard(QFrame):
    """Tarjeta KPI con número grande y label."""

    def __init__(self, title: str, value: str = "0", color: str = "#3498db", parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{"
            f" background-color: #2c3e50;"
            f" border-left: 4px solid {color};"
            f" border-radius: 8px;"
            f" padding: 16px;"
            f" }}"
        )
        self.setMinimumHeight(100)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)

        self.value_label = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(28)
        value_font.setBold(True)
        self.value_label.setFont(value_font)
        self.value_label.setStyleSheet(f"color: {color}; background: transparent;")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.value_label)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #bdc3c7; font-size: 12px; background: transparent;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

    def set_value(self, value: str):
        self.value_label.setText(value)


class UsageDashboardWidget(QWidget):
    """Widget con dashboard de uso, tablas y exportador CSV."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(12)

        # Header con selector de rango
        header = QHBoxLayout()

        title = QLabel("📊 Dashboard de Uso")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #ecf0f1;")
        header.addWidget(title)
        header.addStretch()

        range_lbl = QLabel("Período:")
        range_lbl.setStyleSheet("color: #bdc3c7; font-size: 13px;")
        header.addWidget(range_lbl)

        self.range_combo = QComboBox()
        self.range_combo.setMinimumHeight(36)
        self.range_combo.addItem("Último día", 1)
        self.range_combo.addItem("Últimos 7 días", 7)
        self.range_combo.addItem("Últimos 30 días", 30)
        self.range_combo.addItem("Últimos 90 días", 90)
        self.range_combo.setCurrentIndex(2)
        self.range_combo.currentIndexChanged.connect(self.refresh)
        header.addWidget(self.range_combo)

        refresh_btn = QPushButton("🔄 Actualizar")
        refresh_btn.setMinimumHeight(36)
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn)

        export_btn = QPushButton("📥 Exportar CSV")
        export_btn.setMinimumHeight(36)
        export_btn.setObjectName("PrimaryButton")
        export_btn.clicked.connect(self._export_csv)
        header.addWidget(export_btn)

        main_layout.addLayout(header)

        # KPIs
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)
        self.card_apps = StatCard("Lanzamientos de apps", "0", "#3498db")
        self.card_meetings = StatCard("Eventos reuniones", "0", "#9b59b6")
        self.card_alerts = StatCard("Alertas enviadas", "0", "#f39c12")
        self.card_joined = StatCard("Reuniones unidas", "0", "#27ae60")
        self.card_notifs = StatCard("Notificaciones", "0", "#e74c3c")
        for card in (self.card_apps, self.card_meetings, self.card_alerts, self.card_joined, self.card_notifs):
            kpi_row.addWidget(card, 1)
        main_layout.addLayout(kpi_row)

        # Tabla: uso de aplicaciones
        usage_title = QLabel("Uso de Aplicaciones")
        usage_title.setStyleSheet("color: #3498db; font-size: 14px; font-weight: bold; margin-top: 8px;")
        main_layout.addWidget(usage_title)

        self.usage_table = QTableWidget()
        self.usage_table.setColumnCount(4)
        self.usage_table.setHorizontalHeaderLabels(["Aplicación", "Lanzamientos", "Exitosos", "Errores"])
        self.usage_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.usage_table.verticalHeader().setVisible(False)
        self.usage_table.setStyleSheet(
            "QTableWidget {"
            " background-color: #2c3e50; color: #ecf0f1; gridline-color: #34495e;"
            " border: 1px solid #34495e; border-radius: 6px;"
            "}"
            "QHeaderView::section {"
            " background-color: #34495e; color: #ecf0f1; padding: 8px;"
            " border: none; font-weight: bold;"
            "}"
            "QTableWidget::item { padding: 8px; }"
        )
        self.usage_table.setMinimumHeight(180)
        main_layout.addWidget(self.usage_table)

        # Tabla: historial reciente
        history_title = QLabel("Historial Reciente (últimas 50 acciones)")
        history_title.setStyleSheet("color: #3498db; font-size: 14px; font-weight: bold; margin-top: 8px;")
        main_layout.addWidget(history_title)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["Hora", "Tipo", "Detalle", "Acción", "Info"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setStyleSheet(self.usage_table.styleSheet())
        self.history_table.setMinimumHeight(300)
        main_layout.addWidget(self.history_table, 1)

        # Footer con mantenimiento
        footer = QHBoxLayout()
        cleanup_lbl = QLabel("Retención de datos:")
        cleanup_lbl.setStyleSheet("color: #bdc3c7; font-size: 12px;")
        footer.addWidget(cleanup_lbl)

        self.retention_spin = QSpinBox()
        self.retention_spin.setRange(7, 365)
        self.retention_spin.setValue(90)
        self.retention_spin.setSuffix(" días")
        self.retention_spin.setMinimumHeight(36)
        footer.addWidget(self.retention_spin)

        cleanup_btn = QPushButton("🗑 Limpiar datos antiguos")
        cleanup_btn.setMinimumHeight(36)
        cleanup_btn.setObjectName("DangerButton")
        cleanup_btn.clicked.connect(self._cleanup)
        footer.addWidget(cleanup_btn)

        footer.addStretch()
        main_layout.addLayout(footer)

    def _get_since(self) -> datetime:
        days = self.range_combo.currentData() or 30
        return datetime.now() - timedelta(days=days)

    def refresh(self):
        since = self._get_since()
        try:
            overall = audit.get_overall_stats(since)
            meeting_stats = audit.get_meeting_stats(since)

            self.card_apps.set_value(str(overall.get("app_launches", 0)))
            self.card_meetings.set_value(str(meeting_stats.get("total", 0)))
            self.card_alerts.set_value(str(meeting_stats.get("alerts", 0)))
            self.card_joined.set_value(str(meeting_stats.get("joined", 0)))
            self.card_notifs.set_value(str(overall.get("notifications", 0)))

            self._refresh_usage_table(since)
            self._refresh_history_table(since)
        except Exception as exc:
            logger.error("Error refrescando dashboard: %s", exc, exc_info=True)

    def _refresh_usage_table(self, since: datetime):
        usage = audit.get_app_usage(since)
        self.usage_table.setRowCount(len(usage))
        for row, item in enumerate(usage):
            self.usage_table.setItem(row, 0, QTableWidgetItem(item.get("app_name", "")))
            self.usage_table.setItem(row, 1, QTableWidgetItem(str(item.get("total_launches", 0))))
            self.usage_table.setItem(row, 2, QTableWidgetItem(str(item.get("successful") or 0)))
            errors = item.get("errors") or 0
            err_item = QTableWidgetItem(str(errors))
            if errors > 0:
                err_item.setForeground(Qt.GlobalColor.red)
            self.usage_table.setItem(row, 3, err_item)

    def _refresh_history_table(self, since: datetime):
        events = []
        for app in audit.get_recent_apps(since, limit=50):
            events.append({
                "timestamp": app.get("timestamp", ""),
                "type": "App",
                "detail": app.get("app_name", ""),
                "action": app.get("action", ""),
                "info": app.get("error") or f"pid={app.get('pid', '')}",
            })
        for m in audit.get_recent_meetings(since, limit=30):
            events.append({
                "timestamp": m.get("timestamp", ""),
                "type": "Reunión",
                "detail": m.get("subject", ""),
                "action": m.get("action", ""),
                "info": f"{m.get('start_time', '')}" if m.get("start_time") else "",
            })
        for s in audit.get_recent_sessions(since, limit=20):
            events.append({
                "timestamp": s.get("timestamp", ""),
                "type": "Sesión",
                "detail": s.get("event_type", ""),
                "action": s.get("event_type", ""),
                "info": s.get("details", ""),
            })

        events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        events = events[:50]

        self.history_table.setRowCount(len(events))
        for row, ev in enumerate(events):
            ts = ev.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(ts)
                ts_display = dt.strftime("%d/%m %H:%M:%S")
            except Exception:
                ts_display = ts
            self.history_table.setItem(row, 0, QTableWidgetItem(ts_display))
            self.history_table.setItem(row, 1, QTableWidgetItem(ev.get("type", "")))
            self.history_table.setItem(row, 2, QTableWidgetItem(ev.get("detail", "")))
            action_item = QTableWidgetItem(ev.get("action", ""))
            action = ev.get("action", "")
            color_map = {
                "launch": Qt.GlobalColor.green,
                "close": Qt.GlobalColor.gray,
                "error": Qt.GlobalColor.red,
                "alert": Qt.GlobalColor.yellow,
                "join": Qt.GlobalColor.cyan,
                "start": Qt.GlobalColor.yellow,
                "end": Qt.GlobalColor.gray,
            }
            if action in color_map:
                action_item.setForeground(color_map[action])
            self.history_table.setItem(row, 3, action_item)
            self.history_table.setItem(row, 4, QTableWidgetItem(ev.get("info", "")))

    def _export_csv(self):
        default_name = f"sopantallas_reporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar reporte CSV", default_name, "CSV files (*.csv)"
        )
        if not path:
            return
        days = self.range_combo.currentData() or 30
        success = audit.export_csv(path, days=days)
        if success:
            QMessageBox.information(
                self, "Reporte Exportado",
                f"Reporte guardado en:\n{path}\n\n"
                f"Período: últimos {days} días.",
            )
        else:
            QMessageBox.critical(self, "Error", "No se pudo generar el reporte CSV.")

    def _cleanup(self):
        days = self.retention_spin.value()
        reply = QMessageBox.question(
            self, "Confirmar limpieza",
            f"¿Eliminar todos los registros con más de {days} días de antigüedad?\n"
            f"Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            deleted = audit.cleanup_old_audit(days)
            QMessageBox.information(
                self, "Limpieza completada",
                f"Se eliminaron {deleted} registros antiguos.",
            )
            self.refresh()
