from datetime import datetime
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont

from core.theme_manager import theme_manager
from core.logger import get_logger


logger = get_logger("ui.widgets.room_status_badge")


STATE_FREE = "free"
STATE_IMMINENT = "imminent"
STATE_OCCUPIED = "occupied"


STATE_LABELS = {
    STATE_FREE: "Sala libre",
    STATE_IMMINENT: "Próxima en {minutes} min",
    STATE_OCCUPIED: "En reunión",
}


class RoomStatusBadge(QFrame):
    def __init__(self, calendar_manager=None, parent=None):
        super().__init__(parent)
        self.setObjectName("RoomStatusBadge")
        self._calendar_manager = calendar_manager
        self._tokens = theme_manager.current_tokens()
        self._state = STATE_FREE
        self._next_meeting = None
        self._pulse_anim = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            self._tokens.space_3, self._tokens.space_2,
            self._tokens.space_3, self._tokens.space_2
        )
        layout.setSpacing(self._tokens.space_2)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._dot = QLabel("●")
        self._dot.setObjectName("RoomStatusDot")
        self._dot.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        dot_font = QFont(self._tokens.font_family_body)
        dot_font.setPointSizeF(20.0)
        dot_font.setBold(True)
        self._dot.setFont(dot_font)
        layout.addWidget(self._dot, 0, Qt.AlignmentFlag.AlignVCenter)

        self._label = QLabel(STATE_LABELS[STATE_FREE])
        self._label.setObjectName("RoomStatusLabel")
        self._label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        label_font = QFont(self._tokens.font_family_body)
        label_font.setPointSizeF(self._tokens.type_badge_label)
        label_font.setWeight(self._tokens.weight_semibold)
        label_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.5)
        self._label.setFont(label_font)
        layout.addWidget(self._label, 0, Qt.AlignmentFlag.AlignVCenter)

        self._opacity_effect = QGraphicsOpacityEffect(self._dot)
        self._opacity_effect.setOpacity(1.0)
        self._dot.setGraphicsEffect(self._opacity_effect)

        self._refresh()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(30 * 1000)

        theme_manager.register_listener(self._on_theme_changed)

    def _on_theme_changed(self, theme_id: str):
        self._tokens = theme_manager.current_tokens()
        label_font = QFont(self._tokens.font_family_body)
        label_font.setPointSizeF(self._tokens.type_badge_label)
        label_font.setWeight(self._tokens.weight_semibold)
        label_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.5)
        self._label.setFont(label_font)
        self._apply_state()

    def _refresh(self):
        state, next_meeting = self._evaluate_state()
        self._state = state
        self._next_meeting = next_meeting
        self._apply_state()

    def _evaluate_state(self):
        if not self._calendar_manager:
            return STATE_FREE, None
        try:
            ongoing = self._calendar_manager.get_ongoing_meetings() or []
            if ongoing:
                return STATE_OCCUPIED, ongoing[0]

            minutes_before = 5
            try:
                cfg = self._calendar_manager.config
                if cfg and hasattr(cfg, "get"):
                    minutes_before = int(cfg.get("alert_minutes_before_meeting", 5))
            except Exception:
                pass

            alerts = self._calendar_manager.get_upcoming_alerts(minutes_before) or []
            if alerts:
                mtg = alerts[0]
                mtg_id = mtg.get("id", "")
                if hasattr(self, "_announced_alerts") and mtg_id in self._announced_alerts:
                    return STATE_FREE, None
                if not hasattr(self, "_announced_alerts"):
                    self._announced_alerts = set()
                self._announced_alerts.add(mtg_id)
                start = mtg.get("start_dt")
                if isinstance(start, datetime):
                    now = datetime.now(start.tzinfo) if start.tzinfo else datetime.now()
                    try:
                        delta = (start - now).total_seconds() / 60
                        minutes = max(1, int(delta))
                        return STATE_IMMINENT, {"minutes": minutes, "subject": mtg.get("subject", "")}
                    except Exception as exc:
                        logger.debug("Error calculando minutos hasta reunión: %s", exc)
        except Exception as exc:
            logger.debug("Error evaluando estado de sala: %s", exc)
        return STATE_FREE, None

    def _apply_state(self):
        state = self._state
        self.setProperty("state", state)
        self._dot.setProperty("state", state)
        self._label.setProperty("state", state)
        self.style().unpolish(self)
        self.style().polish(self)
        self._dot.style().unpolish(self._dot)
        self._dot.style().polish(self._dot)
        self._label.style().unpolish(self._label)
        self._label.style().polish(self._label)

        if state == STATE_FREE:
            self._label.setText(STATE_LABELS[STATE_FREE])
            self._stop_pulse()
        elif state == STATE_IMMINENT:
            minutes = (self._next_meeting or {}).get("minutes", 0)
            self._label.setText(STATE_LABELS[STATE_IMMINENT].format(minutes=minutes))
            self._start_pulse()
        elif state == STATE_OCCUPIED:
            self._label.setText(STATE_LABELS[STATE_OCCUPIED])
            self._start_pulse()

    def _start_pulse(self):
        if self._pulse_anim is not None and self._pulse_anim.state() == QPropertyAnimation.State.Running:
            return
        anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        anim.setDuration(int(self._tokens.motion_medium_ms * 2))
        anim.setStartValue(1.0)
        anim.setEndValue(0.35)
        anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        anim.setLoopCount(-1)
        anim.start()
        self._pulse_anim = anim

    def _stop_pulse(self):
        if self._pulse_anim is not None:
            self._pulse_anim.stop()
            self._pulse_anim = None
        self._opacity_effect.setOpacity(1.0)
