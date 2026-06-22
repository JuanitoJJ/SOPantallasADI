"""
screensaver.py — Pantalla de inactividad premium.

Características:
- Reloj grande + fecha
- Quotes corporativas rotativas
- Eventos / aniversarios del día
- Fondo animado (gradiente o video MP4)
- Overlay de partículas flotantes
- Pulso en "toca para continuar"
- Cualquier evento cierra el screensaver
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QGraphicsOpacityEffect
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    QSequentialAnimationGroup, QDateTime
)
from PyQt6.QtGui import QFont

from core.logger import get_logger
from ui.screensaver_quotes import quotes_manager
from ui.screensaver_events import events_manager
from ui.screensaver_particles import ParticleOverlay
from ui.screensaver_video import VideoBackground


logger = get_logger("ui.screensaver")


QUOTE_ROTATION_MS = 12000
EVENT_BANNER_DURATION_MS = 15000


class ScreensaverOverlay(QWidget):
    """Widget fullscreen premium para inactividad."""

    def __init__(self, corporate_name: str = "SISTEMA CORPORATIVO",
                 video_path: str = "",
                 use_particles: bool = True,
                 parent=None):
        super().__init__(parent)
        self.corporate_name = corporate_name
        self._video_path = video_path
        self._use_particles = use_particles
        self._quote_index = -1
        self._setup_ui()
        self._start_animations()
        self._start_rotations()

    def _setup_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setStyleSheet("background-color: #0d1117;")
        self.setCursor(Qt.CursorShape.BlankCursor)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Layout principal que contendrá video/fondo + contenido
        self._root = QWidget(self)
        self._root.setGeometry(0, 0, self.width(), self.height())

        # Fondo: video o gradiente animado
        self._video_bg = VideoBackground(self._video_path, parent=self)
        self._video_bg.setGeometry(0, 0, self.width(), self.height())
        self._video_bg.lower()

        # Partículas
        if self._use_particles:
            self._particles = ParticleOverlay(self, particle_count=50)
            self._particles.setGeometry(0, 0, self.width(), self.height())
            self._particles.lower()
            self._particles.raise_()
            self._video_bg.lower()

        # Banner de evento (oculto por defecto)
        self._event_banner = QFrame(self)
        self._event_banner.setStyleSheet(
            "QFrame {"
            " background: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
            "   stop:0 rgba(52, 152, 219, 0.95),"
            "   stop:1 rgba(46, 204, 113, 0.95));"
            " border-radius: 12px;"
            " padding: 14px 24px;"
            "}"
        )
        self._event_banner.setFixedHeight(80)
        self._event_banner.hide()

        event_layout = QHBoxLayout(self._event_banner)
        event_layout.setContentsMargins(8, 4, 8, 4)
        self._event_icon = QLabel("🎉")
        event_icon_font = QFont()
        event_icon_font.setPointSize(28)
        self._event_icon.setFont(event_icon_font)
        self._event_icon.setStyleSheet("background: transparent;")
        event_layout.addWidget(self._event_icon)

        event_text_layout = QVBoxLayout()
        event_text_layout.setSpacing(0)
        self._event_title = QLabel()
        self._event_title.setStyleSheet(
            "color: white; font-size: 18px; font-weight: bold; background: transparent;"
        )
        self._event_message = QLabel()
        self._event_message.setStyleSheet(
            "color: rgba(255,255,255,0.9); font-size: 13px; background: transparent;"
        )
        event_text_layout.addWidget(self._event_title)
        event_text_layout.addWidget(self._event_message)
        event_layout.addLayout(event_text_layout, 1)

        # Layout central
        self._content_layout = QVBoxLayout(self)
        self._content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._content_layout.setSpacing(20)
        self._content_layout.setContentsMargins(40, 40, 40, 40)

        # Espaciador superior
        self._content_layout.addStretch(2)

        # Logo / Nombre corporativo
        self.name_label = QLabel(self.corporate_name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet(
            "color: #ecf0f1; font-size: 64px; font-weight: 300; letter-spacing: 8px;"
        )
        self.name_label.setWordWrap(True)
        self._content_layout.addWidget(self.name_label)

        # Reloj
        self.clock_label = QLabel()
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.clock_label.setStyleSheet(
            "color: #3498db; font-size: 130px; font-weight: bold;"
        )
        self._content_layout.addWidget(self.clock_label)

        # Fecha
        self.date_label = QLabel()
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date_label.setStyleSheet(
            "color: #bdc3c7; font-size: 28px; font-weight: 300;"
        )
        self._content_layout.addWidget(self.date_label)

        # Espaciador
        self._content_layout.addSpacing(30)

        # Quote container con borde sutil
        self.quote_frame = QFrame()
        self.quote_frame.setStyleSheet(
            "QFrame {"
            " background-color: rgba(0, 0, 0, 0.4);"
            " border-left: 4px solid #3498db;"
            " border-radius: 6px;"
            " padding: 16px 24px;"
            "}"
        )
        self.quote_frame.setMaximumWidth(900)
        quote_layout = QVBoxLayout(self.quote_frame)
        quote_layout.setSpacing(4)

        self.quote_text = QLabel()
        self.quote_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.quote_text.setStyleSheet(
            "color: #ecf0f1; font-size: 22px; font-style: italic; background: transparent;"
        )
        self.quote_text.setWordWrap(True)
        quote_layout.addWidget(self.quote_text)

        self.quote_author = QLabel()
        self.quote_author.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.quote_author.setStyleSheet(
            "color: #7f8c8d; font-size: 14px; background: transparent; margin-top: 6px;"
        )
        quote_layout.addWidget(self.quote_author)

        # Centrar el quote
        quote_outer = QHBoxLayout()
        quote_outer.addStretch()
        quote_outer.addWidget(self.quote_frame)
        quote_outer.addStretch()
        self._content_layout.addLayout(quote_outer)

        self._content_layout.addStretch(3)

        # Mensaje inferior
        self.touch_label = QLabel("✦ Toca la pantalla para continuar ✦")
        self.touch_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.touch_label.setStyleSheet(
            "color: #4a5568; font-size: 20px; font-style: italic;"
        )
        self._content_layout.addWidget(self.touch_label)

        # Timer del reloj
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._update_clock()

        # Timer de rotación de quotes
        self._quote_timer = QTimer(self)
        self._quote_timer.timeout.connect(self._rotate_quote)
        self._quote_timer.start(QUOTE_ROTATION_MS)
        self._rotate_quote()

        # Timer de hide del banner de evento
        self._event_hide_timer = QTimer(self)
        self._event_hide_timer.setSingleShot(True)
        self._event_hide_timer.timeout.connect(self._hide_event_banner)

        # Verificar evento del día
        self._check_today_event()

    def _check_today_event(self):
        event = events_manager.get_today_event()
        if event:
            self._show_event_banner(event)

    def _show_event_banner(self, event: dict):
        title = event.get("title", "")
        message = event.get("message", "")
        self._event_title.setText(title)
        self._event_message.setText(message)
        self._event_banner.adjustSize()
        # Posicionar en la parte superior
        banner_width = min(700, self.width() - 80)
        self._event_banner.setFixedWidth(banner_width)
        x = (self.width() - banner_width) // 2
        self._event_banner.move(x, 30)
        self._event_banner.show()
        # Animación de entrada
        effect = QGraphicsOpacityEffect(self._event_banner)
        self._event_banner.setGraphicsEffect(effect)
        effect.setOpacity(0.0)
        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(800)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        self._banner_fade_in = anim

        # Auto-ocultar tras N segundos
        self._event_hide_timer.start(EVENT_BANNER_DURATION_MS)

    def _hide_event_banner(self):
        effect = self._event_banner.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(self._event_banner)
            self._event_banner.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(500)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InCubic)
        anim.finished.connect(self._event_banner.hide)
        anim.start()
        self._banner_fade_out = anim

    def _rotate_quote(self):
        quote = quotes_manager.get_random()
        self.quote_text.setText(f"\u201C{quote}\u201D")
        self.quote_author.setText("— Equipo")

    def _update_clock(self):
        now = QDateTime.currentDateTime()
        self.clock_label.setText(now.toString("HH:mm"))
        try:
            date_text = now.toString("dddd, d 'de' MMMM").capitalize()
        except Exception:
            date_text = now.toString("dddd, d MMMM").capitalize()
        self.date_label.setText(date_text)

    def _start_animations(self):
        # Pulso en "toca para continuar"
        effect = QGraphicsOpacityEffect(self.touch_label)
        self.touch_label.setGraphicsEffect(effect)

        fade_out = QPropertyAnimation(effect, b"opacity")
        fade_out.setDuration(1200)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.2)
        fade_out.setEasingCurve(QEasingCurve.Type.InOutSine)

        fade_in = QPropertyAnimation(effect, b"opacity")
        fade_in.setDuration(1200)
        fade_in.setStartValue(0.2)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.InOutSine)

        self._pulse_group = QSequentialAnimationGroup(self)
        self._pulse_group.addAnimation(fade_out)
        self._pulse_group.addAnimation(fade_in)
        self._pulse_group.setLoopCount(-1)
        self._pulse_group.start()

    def _start_rotations(self):
        pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._root.setGeometry(0, 0, self.width(), self.height())
        if hasattr(self, '_video_bg') and self._video_bg is not None:
            self._video_bg.setGeometry(0, 0, self.width(), self.height())
        if hasattr(self, '_particles') and self._particles is not None:
            self._particles.setGeometry(0, 0, self.width(), self.height())
        if hasattr(self, '_event_banner') and self._event_banner.isVisible():
            banner_width = min(700, self.width() - 80)
            self._event_banner.setFixedWidth(banner_width)
            x = (self.width() - banner_width) // 2
            self._event_banner.move(x, 30)

    def show_animated(self):
        self.showFullScreen()
        self.activateWindow()
        self.setFocus()

        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(700)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim.finished.connect(lambda: self.setGraphicsEffect(None))
        anim.start()
        self._fade_in_anim = anim

    def mousePressEvent(self, a0):
        self._dismiss()

    def mouseMoveEvent(self, a0):
        self._dismiss()

    def touchEvent(self, a0):
        self._dismiss()

    def keyPressEvent(self, a0):
        self._dismiss()

    def _dismiss(self):
        # Detener partículas y video
        if hasattr(self, '_particles') and self._particles is not None:
            self._particles.stop()
        if hasattr(self, '_video_bg') and self._video_bg is not None:
            self._video_bg.stop()

        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(350)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim.finished.connect(self.hide)
        anim.finished.connect(lambda: self.setGraphicsEffect(None))
        if callable(getattr(self, '_dismiss_callback', None)):
            anim.finished.connect(self._dismiss_callback)
        anim.start()
        self._fade_out_anim = anim


class InactivityManager:
    """Detecta inactividad y activa ScreensaverOverlay tras X minutos."""

    DEFAULT_TIMEOUT_MINUTES = 5

    def __init__(self, parent_window, corporate_name: str,
                 timeout_minutes: int = DEFAULT_TIMEOUT_MINUTES,
                 video_path: str = "",
                 use_particles: bool = True):
        self._parent = parent_window
        self._timeout_ms = timeout_minutes * 60 * 1000
        self._video_path = video_path
        self._use_particles = use_particles

        self._screensaver = ScreensaverOverlay(
            corporate_name,
            video_path=self._video_path,
            use_particles=self._use_particles,
            parent=None,
        )

        self._timer = QTimer(parent_window)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._activate)
        self._timer.start(self._timeout_ms)

    def reset(self):
        self._timer.start(self._timeout_ms)

    def set_timeout(self, minutes: int):
        self._timeout_ms = minutes * 60 * 1000
        self._timer.start(self._timeout_ms)

    def set_video(self, video_path: str):
        self._video_path = video_path
        # Recrear screensaver con nuevo video
        if self._screensaver is not None:
            self._screensaver.deleteLater()
        self._screensaver = ScreensaverOverlay(
            "SISTEMA CORPORATIVO",
            video_path=self._video_path,
            use_particles=self._use_particles,
            parent=None,
        )
        self._screensaver._dismiss_callback = self.reset

    def _activate(self):
        self._screensaver.show_animated()
        self._screensaver._dismiss_callback = self.reset
