"""
animations.py — Helpers para animaciones suaves y consistentes.

Estándares de duración:
- INSTANT: <100ms (feedback inmediato)
- FAST: 150-250ms (hover, focus)
- NORMAL: 300-400ms (transiciones de UI)
- SLOW: 500-800ms (apertura/cierre de diálogos)
- EXTRA_SLOW: 1000+ms (efectos especiales)
"""
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QPoint, QRect, QSize
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QWidget


DURATIONS = {
    "instant": 80,
    "fast": 200,
    "normal": 350,
    "slow": 600,
    "extra_slow": 1000,
}

EASING = {
    "linear": QEasingCurve.Type.Linear,
    "in_quad": QEasingCurve.Type.InQuad,
    "out_quad": QEasingCurve.Type.OutQuad,
    "in_out_quad": QEasingCurve.Type.InOutQuad,
    "out_cubic": QEasingCurve.Type.OutCubic,
    "in_out_cubic": QEasingCurve.Type.InOutCubic,
    "out_back": QEasingCurve.Type.OutBack,
    "out_bounce": QEasingCurve.Type.OutBounce,
    "out_elastic": QEasingCurve.Type.OutElastic,
}


def fade_in(widget: QWidget, duration: str = "normal", on_finished=None):
    """Fade-in con opacidad 0→1."""
    return animate_opacity(widget, 0.0, 1.0, duration, on_finished)


def fade_out(widget: QWidget, duration: str = "normal", on_finished=None):
    """Fade-out con opacidad 1→0."""
    return animate_opacity(widget, 1.0, 0.0, duration, on_finished)


def animate_opacity(widget: QWidget, start: float, end: float,
                    duration: str = "normal", on_finished=None):
    """Anima opacidad con curva estándar."""
    effect = widget.graphicsEffect()
    if not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
    effect.setOpacity(start)
    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(DURATIONS.get(duration, 350))
    anim.setStartValue(start)
    anim.setEndValue(end)
    anim.setEasingCurve(EASING["in_out_cubic"])
    if on_finished:
        anim.finished.connect(on_finished)
    anim.start()
    # Guardar referencia en widget para evitar GC
    widget._anim = anim
    return anim


def scale_in(widget: QWidget, duration: str = "normal", on_finished=None):
    """Efecto de escala 0.85→1.0 combinado con fade-in."""
    effect = widget.graphicsEffect()
    if not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
    effect.setOpacity(0.0)
    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(DURATIONS.get(duration, 350))
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(EASING["out_cubic"])
    if on_finished:
        anim.finished.connect(on_finished)
    anim.start()
    widget._anim = anim
    return anim


def slide_in_from_right(widget: QWidget, parent_width: int,
                         duration: str = "normal", on_finished=None):
    """Slide desde la derecha."""
    end_pos = widget.pos()
    start_pos = QPoint(parent_width, end_pos.y())
    widget.move(start_pos)
    anim = QPropertyAnimation(widget, b"pos")
    anim.setDuration(DURATIONS.get(duration, 350))
    anim.setStartValue(start_pos)
    anim.setEndValue(end_pos)
    anim.setEasingCurve(EASING["out_cubic"])
    if on_finished:
        anim.finished.connect(on_finished)
    anim.start()
    widget._anim = anim
    return anim


def pulse(widget: QWidget, scale_min: float = 0.95, scale_max: float = 1.05,
          cycles: int = 1, duration_per_cycle: int = 600):
    """Pulso de escala (no implementado con transform, pero simula con opacidad)."""
    effect = widget.graphicsEffect()
    if not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
    from PyQt6.QtCore import QSequentialAnimationGroup
    group = QSequentialAnimationGroup(widget)
    for _ in range(cycles):
        a = QPropertyAnimation(effect, b"opacity")
        a.setDuration(duration_per_cycle // 2)
        a.setStartValue(1.0)
        a.setEndValue(0.5)
        a.setEasingCurve(EASING["in_out_quad"])
        group.addAnimation(a)
        b = QPropertyAnimation(effect, b"opacity")
        b.setDuration(duration_per_cycle // 2)
        b.setStartValue(0.5)
        b.setEndValue(1.0)
        b.setEasingCurve(EASING["in_out_quad"])
        group.addAnimation(b)
    group.start()
    widget._anim = group
    return group


def staggered_fade_in(widgets: list, stagger_ms: int = 80,
                      duration: str = "normal"):
    """Fade-in escalonado para listas de widgets."""
    from PyQt6.QtCore import QTimer
    animations = []
    for i, w in enumerate(widgets):
        if i == 0:
            fade_in(w, duration=duration)
        else:
            QTimer.singleShot(
                i * stagger_ms,
                lambda widget=w: fade_in(widget, duration=duration),
            )
        animations.append(w)
    return animations
