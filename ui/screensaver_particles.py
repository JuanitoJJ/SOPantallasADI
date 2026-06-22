import random
import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush


class Particle:
    def __init__(self, width: int, height: int):
        self.x = random.uniform(0, width)
        self.y = random.uniform(0, height)
        self.vx = random.uniform(-0.3, 0.3)
        self.vy = random.uniform(-0.5, -0.1)
        self.size = random.uniform(2, 5)
        self.alpha = random.uniform(0.3, 0.8)
        self.life = 1.0
        self.decay = random.uniform(0.0008, 0.0015)
        self.color = QColor(
            random.randint(180, 220),
            random.randint(200, 240),
            random.randint(220, 255),
        )

    def update(self, width: int, height: int):
        self.x += self.vx
        self.y += self.vy
        self.life -= self.decay
        if self.life <= 0 or self.y < -10 or self.x < -10 or self.x > width + 10:
            self._respawn(width, height)

    def _respawn(self, width: int, height: int):
        self.x = random.uniform(0, width)
        self.y = height + random.uniform(0, 30)
        self.vx = random.uniform(-0.3, 0.3)
        self.vy = random.uniform(-0.5, -0.1)
        self.size = random.uniform(2, 5)
        self.alpha = random.uniform(0.3, 0.8)
        self.life = 1.0
        self.decay = random.uniform(0.0008, 0.0015)


class ParticleOverlay(QWidget):
    """Overlay transparente con partículas flotando hacia arriba."""

    def __init__(self, parent=None, particle_count: int = 60):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self._particles = []
        self._particle_count = particle_count
        self._init_particles(0, 0)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(33)

    def _init_particles(self, width: int, height: int):
        self._particles = [
            Particle(width or 1920, height or 1080)
            for _ in range(self._particle_count)
        ]

    def _on_tick(self):
        w = self.width()
        h = self.height()
        for p in self._particles:
            p.update(w, h)
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self._particles or len(self._particles) != self._particle_count:
            self._init_particles(self.width(), self.height())

    def paintEvent(self, event):
        if not self._particles:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        for p in self._particles:
            color = QColor(p.color)
            color.setAlphaF(p.alpha * p.life)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(p.x, p.y), p.size, p.size)
        painter.end()

    def stop(self):
        self._timer.stop()
