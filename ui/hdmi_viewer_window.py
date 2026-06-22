"""
hdmi_viewer_window.py — Ventana flotante que muestra la entrada HDMI.

Características:
- Frameless, arrastrable desde la barra superior
- Botón X cerrar (esquina superior derecha)
- Botón minimizar
- QLabel central scaledContents para el video
- Footer con estado (conectado / sin señal / error) + grip de resize
- Tamaño inicial 80% × 70% del screen principal, centrada
- Doble click en barra → toggle fullscreen / flotante
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QSizePolicy, QGraphicsOpacityEffect)
from PyQt6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QPixmap, QCursor, QFont

from core.logger import get_logger
from core.hdmi_capture import (HDMICaptureManager, get_capture_manager,
                               STATE_CONNECTED, STATE_NO_SIGNAL,
                               STATE_CONNECTING, STATE_ERROR, STATE_CLOSED)
from core import audit


logger = get_logger("ui.hdmi_viewer_window")


STATE_LABELS = {
    STATE_CONNECTING: ("🟡 Conectando...", "#f39c12"),
    STATE_CONNECTED: ("🟢 Señal activa", "#27ae60"),
    STATE_NO_SIGNAL: ("🟡 Sin señal — Conecta un cable HDMI", "#f39c12"),
    STATE_ERROR: ("🔴 Error de captura", "#e74c3c"),
    STATE_CLOSED: ("⚫ Cerrado", "#7f8c8d"),
}


class HDMIViewerWindow(QWidget):
    """Ventana flotante que muestra la captura HDMI."""

    closed = pyqtSignal()

    def __init__(self, device_index: int, width: int, height: int, fps: int,
                 parent=None):
        super().__init__(parent)
        self._device_index = device_index
        self._width = width
        self._height = height
        self._fps = fps
        self._drag_pos: QPoint = None
        self._is_fullscreen = False
        self._session_started_ts = None

        self._manager = get_capture_manager()
        self._manager.configure(device_index, width, height, fps)

        self._build_ui()
        self._center_on_screen()

        self._manager.frame_ready.connect(self._on_frame)
        self._manager.state_changed.connect(self._on_state_changed)

        self._set_state(STATE_CONNECTING)
        self._manager.start()
        self._log_session_start()

    def _build_ui(self):
        """Construye la UI: barra superior + video + footer."""
        self.setWindowTitle("Compartir Pantalla — HDMI Input")
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setMinimumSize(480, 320)
        self.setStyleSheet("""
            QWidget#HDMIMainFrame {
                background-color: #1a1a1a;
                border: 2px solid #3498db;
                border-radius: 10px;
            }
            QLabel#HDMITitle {
                color: white;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
                padding-left: 8px;
            }
            QPushButton#HDMICloseBtn {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
                padding: 4px;
                min-width: 36px;
                max-width: 36px;
                min-height: 32px;
                max-height: 32px;
            }
            QPushButton#HDMICloseBtn:hover {
                background-color: #c0392b;
            }
            QPushButton#HDMICloseBtn:pressed {
                background-color: #a93226;
            }
            QPushButton#HDMIMinBtn {
                background-color: #34495e;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
                padding: 4px;
                min-width: 36px;
                max-width: 36px;
                min-height: 32px;
                max-height: 32px;
            }
            QPushButton#HDMIMinBtn:hover {
                background-color: #3d566e;
            }
            QPushButton#HDMIMaxBtn {
                background-color: #34495e;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
                padding: 4px;
                min-width: 36px;
                max-width: 36px;
                min-height: 32px;
                max-height: 32px;
            }
            QPushButton#HDMIMaxBtn:hover {
                background-color: #3d566e;
            }
            QLabel#HDMIStatus {
                color: #bdc3c7;
                font-size: 12px;
                background: transparent;
                padding-left: 10px;
            }
            QLabel#HDMIResize {
                background: transparent;
                color: #7f8c8d;
                font-size: 14px;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._main_frame = QWidget()
        self._main_frame.setObjectName("HDMIMainFrame")
        frame_layout = QVBoxLayout(self._main_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)

        # ── Barra superior ──────────────────────────────────────
        self._title_bar = QWidget()
        self._title_bar.setFixedHeight(40)
        self._title_bar.setStyleSheet(
            "background-color: #2c3e50; border-top-left-radius: 8px; "
            "border-top-right-radius: 8px;"
        )
        title_layout = QHBoxLayout(self._title_bar)
        title_layout.setContentsMargins(8, 0, 8, 0)
        title_layout.setSpacing(4)

        title_icon = QLabel("🖥️")
        title_icon.setStyleSheet(
            "color: white; font-size: 16px; background: transparent;"
        )
        title_layout.addWidget(title_icon)

        self._title_label = QLabel("Compartir pantalla")
        self._title_label.setObjectName("HDMITitle")
        title_layout.addWidget(self._title_label, 1)

        self._min_btn = QPushButton("─")
        self._min_btn.setObjectName("HDMIMinBtn")
        self._min_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._min_btn.setToolTip("Minimizar")
        self._min_btn.clicked.connect(self.showMinimized)
        title_layout.addWidget(self._min_btn)

        self._max_btn = QPushButton("☐")
        self._max_btn.setObjectName("HDMIMaxBtn")
        self._max_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._max_btn.setToolTip("Maximizar / Restaurar")
        self._max_btn.clicked.connect(self._toggle_fullscreen)
        title_layout.addWidget(self._max_btn)

        self._close_btn = QPushButton("✕")
        self._close_btn.setObjectName("HDMICloseBtn")
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.setToolTip("Cerrar")
        self._close_btn.clicked.connect(self.close)
        title_layout.addWidget(self._close_btn)

        frame_layout.addWidget(self._title_bar)

        # ── Video ──────────────────────────────────────────────
        self._video_label = QLabel()
        self._video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._video_label.setStyleSheet(
            "background-color: #000000; color: #7f8c8d; "
            "font-size: 18px; font-style: italic;"
        )
        self._video_label.setText("Esperando señal HDMI...")
        self._video_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        frame_layout.addWidget(self._video_label, 1)

        # ── Footer ─────────────────────────────────────────────
        self._footer = QWidget()
        self._footer.setFixedHeight(32)
        self._footer.setStyleSheet(
            "background-color: #2c3e50; border-bottom-left-radius: 8px; "
            "border-bottom-right-radius: 8px;"
        )
        footer_layout = QHBoxLayout(self._footer)
        footer_layout.setContentsMargins(8, 0, 8, 0)
        footer_layout.setSpacing(4)

        self._status_label = QLabel("")
        self._status_label.setObjectName("HDMIStatus")
        footer_layout.addWidget(self._status_label, 1)

        self._resize_grip = QLabel("⤡")
        self._resize_grip.setObjectName("HDMIResize")
        self._resize_grip.setCursor(Qt.CursorShape.SizeFDiagCursor)
        footer_layout.addWidget(self._resize_grip)

        frame_layout.addWidget(self._footer)

        main_layout.addWidget(self._main_frame)

        # Tamaño inicial: 80% × 70% del screen
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            avail = screen.availableGeometry()
            init_w = int(avail.width() * 0.8)
            init_h = int(avail.height() * 0.7)
            self.resize(init_w, init_h)

    def _center_on_screen(self):
        """Centra la ventana en la pantalla principal."""
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            avail = screen.availableGeometry()
            x = avail.x() + (avail.width() - self.width()) // 2
            y = avail.y() + (avail.height() - self.height()) // 2
            self.move(x, y)

    # ── Signals del manager ───────────────────────────────────────
    def _on_frame(self, qimage):
        if qimage is None or qimage.isNull():
            return
        pix = QPixmap.fromImage(qimage)
        scaled = pix.scaled(
            self._video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._video_label.setPixmap(scaled)
        self._video_label.setText("")

    def _on_state_changed(self, state: str):
        self._set_state(state)

    def _set_state(self, state: str):
        label, color = STATE_LABELS.get(state, ("?", "#7f8c8d"))
        self._status_label.setText(label)
        self._status_label.setStyleSheet(
            f"color: {color}; font-size: 12px; "
            f"font-weight: bold; background: transparent; padding-left: 10px;"
        )

        if state == STATE_NO_SIGNAL and self._video_label.pixmap() is None:
            self._video_label.setText("🟡 Sin señal — Conecta un cable HDMI")
        elif state == STATE_ERROR:
            self._video_label.setText("🔴 Error al abrir el dispositivo")
        elif state == STATE_CONNECTING:
            self._video_label.setText("⏳ Conectando...")

    # ── Auditoría ────────────────────────────────────────────────
    def _log_session_start(self):
        try:
            details = (
                f"device_index={self._device_index}, "
                f"resolution={self._width}x{self._height}, fps={self._fps}"
            )
            audit.log_hdmi_session_start(details)
            import time
            self._session_started_ts = time.monotonic()
            logger.info("Sesión HDMI iniciada: %s", details)
        except Exception as exc:
            logger.debug("Error registrando sesión HDMI: %s", exc)

    def _log_session_end(self):
        if self._session_started_ts is None:
            return
        try:
            import time
            duration = time.monotonic() - self._session_started_ts
            audit.log_hdmi_session_end(int(duration))
            logger.info("Sesión HDMI cerrada (duración: %ds)", int(duration))
        except Exception as exc:
            logger.debug("Error registrando cierre sesión HDMI: %s", exc)
        finally:
            self._session_started_ts = None

    # ── Drag / resize ────────────────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._title_bar.underMouse():
                if self._is_fullscreen:
                    event.ignore()
                    return
                self._drag_pos = (
                    event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                )
                event.accept()
                return
            if self._resize_grip.underMouse():
                self._resize_pos = event.globalPosition().toPoint()
                self._resize_size = self.size()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            if self._drag_pos is not None and not self._is_fullscreen:
                self.move(event.globalPosition().toPoint() - self._drag_pos)
                event.accept()
                return
            if hasattr(self, '_resize_pos') and self._resize_pos is not None:
                delta = event.globalPosition().toPoint() - self._resize_pos
                new_w = max(self.minimumWidth(), self._resize_size.width() + int(delta.x()))
                new_h = max(self.minimumHeight(), self._resize_size.height() + int(delta.y()))
                self.resize(new_w, new_h)
                event.accept()
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._drag_pos is not None:
                self._drag_pos = None
            if hasattr(self, '_resize_pos') and self._resize_pos is not None:
                self._resize_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._title_bar.underMouse():
            self._toggle_fullscreen()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def _toggle_fullscreen(self):
        if self._is_fullscreen:
            self.showNormal()
            self._is_fullscreen = False
            self._title_label.setText("Compartir pantalla")
            self._max_btn.setText("☐")
            self._max_btn.setToolTip("Maximizar")
        else:
            self.showFullScreen()
            self._is_fullscreen = True
            self._title_label.setText("Compartir pantalla (fullscreen — doble click para salir)")
            self._max_btn.setText("❐")
            self._max_btn.setToolTip("Restaurar")

    # ── Cierre ───────────────────────────────────────────────────
    def closeEvent(self, event):
        self._log_session_end()
        try:
            self._manager.frame_ready.disconnect(self._on_frame)
            self._manager.state_changed.disconnect(self._on_state_changed)
        except Exception:
            pass
        try:
            self._manager.stop()
        except Exception as exc:
            logger.debug("Error deteniendo manager: %s", exc)
        if self.closed is not None:
            try:
                self.closed.emit()
            except Exception:
                pass
        super().closeEvent(event)

    def force_stop(self):
        """Llamado desde fuera (ej: Finalizar Reunión) para detener sin emitir eventos."""
        self._log_session_end()
        try:
            self._manager.stop()
        except Exception:
            pass
        self.close()