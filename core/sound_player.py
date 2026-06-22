import os
import threading
from core.logger import get_logger


logger = get_logger("core.sound_player")


SOUND_DIR = "assets/sounds"
DEFAULT_SOUNDS = {
    "info": "info.wav",
    "warning": "warning.wav",
    "error": "error.wav",
    "success": "success.wav",
    "meeting": "meeting.wav",
}


_sound_cache = {}


def _get_sound_path(sound_type: str, custom_path: str = "") -> str:
    if custom_path and os.path.exists(custom_path):
        return custom_path
    default_file = DEFAULT_SOUNDS.get(sound_type, "info.wav")
    candidates = [
        os.path.join(SOUND_DIR, default_file),
        os.path.join(".", SOUND_DIR, default_file),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return ""


def _play_in_thread(sound_path: str):
    def _play():
        try:
            import winsound
            flags = winsound.SND_FILENAME | winsound.SND_ASYNC
            if sound_path.lower().endswith(".wav"):
                winsound.PlaySound(sound_path, flags)
            else:
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except ImportError:
            try:
                from PyQt6.QtMultimedia import QSoundEffect
                from PyQt6.QtCore import QUrl
                effect = QSoundEffect()
                effect.setSource(QUrl.fromLocalFile(sound_path))
                effect.setVolume(0.7)
                effect.play()
                _sound_cache[id(effect)] = effect
            except Exception as exc:
                logger.debug("QtMultimedia no disponible: %s", exc)
        except Exception as exc:
            logger.debug("Error reproduciendo sonido: %s", exc)

    t = threading.Thread(target=_play, daemon=True)
    t.start()


def play_notification_sound(sound_type: str = "info"):
    from core.config_manager import ConfigManager
    try:
        config = ConfigManager()
    except Exception:
        config = None

    enabled = True
    custom_path = ""
    if config:
        cfg = config.config
        enabled = cfg.get("notification_sound_enabled", True)
        custom_path = cfg.get("notification_sound_path", "")

    if not enabled:
        return

    sound_path = _get_sound_path(sound_type, custom_path)
    if sound_path:
        _play_in_thread(sound_path)
    else:
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            pass
