import os
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtGui import QPainter, QColor, QBrush
from core.logger import get_logger


logger = get_logger("ui.screensaver.video_bg")


class VideoBackground(QWidget):
    """Widget que intenta reproducir video MP4 como fondo.
    Si QtMultimedia no está disponible, muestra fondo de fallback con gradiente.
    """

    def __init__(self, video_path: str = "", parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._video_path = video_path
        self._media_player = None
        self._video_widget = None
        self._fallback_mode = True
        self._gradient_step = 0.0
        self._init_player()

        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._on_anim_tick)
        self._anim_timer.start(50)

    def _init_player(self):
        if not self._video_path or not os.path.exists(self._video_path):
            logger.info("Video path no disponible, usando fondo con gradiente animado")
            return
        try:
            from PyQt6.QtMultimedia import QMediaPlayer
            from PyQt6.QtMultimediaWidgets import QVideoWidget
            from PyQt6.QtCore import QPoint

            self._video_widget = QVideoWidget(self)
            self._video_widget.setGeometry(0, 0, self.width(), self.height())
            self._media_player = QMediaPlayer(self)
            self._media_player.setVideoOutput(self._video_widget)
            self._media_player.setSource(QUrl.fromLocalFile(os.path.abspath(self._video_path)))
            self._media_player.setLoops(QMediaPlayer.Loops.Infinite)
            self._media_player.play()
            self._fallback_mode = False
            logger.info("Video de fondo cargado: %s", self._video_path)
        except ImportError:
            logger.warning("QtMultimedia no disponible, usando fallback")
        except Exception as exc:
            logger.warning("Error inicializando video: %s, usando fallback", exc)

    def is_playing(self) -> bool:
        return self._media_player is not None and not self._fallback_mode

    def _on_anim_tick(self):
        if self._fallback_mode:
            self._gradient_step = (self._gradient_step + 0.005) % 1.0
            self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._video_widget is not None:
            self._video_widget.setGeometry(0, 0, self.width(), self.height())

    def paintEvent(self, event):
        if not self._fallback_mode:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        import math
        offset = math.sin(self._gradient_step * math.pi * 2) * 30

        c1 = QColor(13, 17, 23)
        c2 = QColor(20 + int(offset), 30 + int(offset), 50 + int(offset))
        c3 = QColor(13, 17, 23)

        grad = QBrush()
        from PyQt6.QtGui import QLinearGradient
        linear = QLinearGradient(0, 0, w, h)
        linear.setColorAt(0.0, c1)
        linear.setColorAt(0.5, c2)
        linear.setColorAt(1.0, c3)
        painter.fillRect(0, 0, w, h, QBrush(linear))
        painter.end()

    def stop(self):
        if self._media_player is not None:
            try:
                self._media_player.stop()
            except Exception:
                pass
        self._anim_timer.stop()
