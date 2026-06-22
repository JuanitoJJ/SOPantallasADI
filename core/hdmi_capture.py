"""
hdmi_capture.py — Captura de video desde un dispositivo HDMI (DirectShow).

Utiliza OpenCV (cv2.VideoCapture con backend CAP_DSHOW) para leer frames de
la tarjeta de captura que aparece en Windows al conectar un cable HDMI al
puerto de entrada de la pantalla interactiva.

Funcionamiento:
- HDMICaptureManager es un QObject con signals (`frame_ready`, `state_changed`)
- El lector corre en un hilo dedicado (threading.Thread) para no bloquear la UI
- Emite QImage en formato RGB888 listo para QLabel.setPixmap
- Detecta "sin señal" si cap.read() falla >2s consecutivos
- Libera el recurso correctamente al detener

Uso:
    manager = HDMICaptureManager()
    manager.frame_ready.connect(my_widget.on_frame)
    manager.state_changed.connect(my_widget.on_state)
    manager.configure(device_index=0, width=1920, height=1080, fps=30)
    manager.start()
    ...
    manager.stop()
"""
import threading
import time

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QImage

from core.logger import get_logger

try:
    import cv2
    # Silenciar warnings de OpenCV (se imprimen a stderr en cada intento de abrir)
    try:
        cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)
    except AttributeError:
        pass
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False


logger = get_logger("core.hdmi_capture")


STATE_CONNECTING = "connecting"
STATE_CONNECTED = "connected"
STATE_NO_SIGNAL = "no_signal"
STATE_ERROR = "error"
STATE_CLOSED = "closed"

_NO_SIGNAL_TIMEOUT_S = 2.0


class HDMICaptureManager(QObject):
    """Singleton para captura de video HDMI vía DirectShow."""

    frame_ready = pyqtSignal('QImage')
    state_changed = pyqtSignal(str)

    _instance = None
    _initialized = False

    @classmethod
    def instance(cls):
        """Devuelve (o crea) la instancia singleton."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if HDMICaptureManager._initialized:
            return
        super().__init__()
        HDMICaptureManager._initialized = True

        self._device_index: int = 0
        self._width: int = 1920
        self._height: int = 1080
        self._fps: int = 30

        self._cap = None
        self._reader_thread: threading.Thread = None
        self._stop_event = threading.Event()
        self._state: str = STATE_CLOSED
        self._last_success_ts: float = 0.0
        self._last_emit_ts: float = 0.0
        self._frame_interval: float = 1.0 / 30.0
        self._lock = threading.Lock()
        self._no_signal_timer: float = 0.0

    # ── API pública ──────────────────────────────────────────────
    @staticmethod
    def is_available() -> bool:
        """True si opencv-python está instalado."""
        return _CV2_AVAILABLE

    @staticmethod
    def list_devices() -> list:
        """Enumera dispositivos de captura DirectShow disponibles.

        Devuelve lista de dicts: [{"index": 0, "name": "..."}, ...]
        Limita la búsqueda a 8 índices (más que suficiente para una sala).
        Usa timeout por dispositivo para no colgarse si OpenCV
        no responde (driver roto, sin dispositivo, etc.).
        """
        if not _CV2_AVAILABLE:
            logger.warning("OpenCV no está disponible")
            return []

        devices = []
        max_index = 8
        probe_timeout_s = 2.0

        for index in range(max_index):
            result = {"opened": False, "backend": "DSHOW", "error": None}
            probe_thread = None

            def _probe(idx=index, res=result):
                cap = None
                try:
                    cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
                    res["opened"] = cap.isOpened()
                    if cap.isOpened() and hasattr(cap, 'getBackendName'):
                        try:
                            res["backend"] = cap.getBackendName()
                        except Exception:
                            pass
                except Exception as exc:
                    res["error"] = str(exc)
                finally:
                    if cap is not None:
                        try:
                            cap.release()
                        except Exception:
                            pass

            probe_thread = threading.Thread(target=_probe, daemon=True)
            probe_thread.start()
            probe_thread.join(timeout=probe_timeout_s)

            if probe_thread.is_alive():
                logger.debug(
                    "Timeout al sondear dispositivo %d (OpenCV no responde)",
                    index,
                )
                continue

            if result["opened"]:
                devices.append({
                    "index": index,
                    "name": f"Dispositivo {index} ({result['backend']})",
                })

        return devices

    def configure(self, device_index: int, width: int = 1920,
                  height: int = 1080, fps: int = 30):
        """Guarda la configuración del dispositivo. No abre hasta start()."""
        with self._lock:
            self._device_index = int(device_index)
            self._width = int(width)
            self._height = int(height)
            self._fps = max(1, int(fps))
            self._frame_interval = 1.0 / self._fps
        logger.info(
            "HDMI configurado: device=%d, %dx%d @ %d fps",
            self._device_index, self._width, self._height, self._fps,
        )

    def is_running(self) -> bool:
        return self._reader_thread is not None and self._reader_thread.is_alive()

    def current_state(self) -> str:
        return self._state

    def start(self):
        """Abre el dispositivo y lanza el hilo lector."""
        if not _CV2_AVAILABLE:
            self._emit_state(STATE_ERROR)
            logger.error("OpenCV no disponible, no se puede iniciar captura HDMI")
            return False

        if self.is_running():
            logger.debug("HDMI capture ya está en ejecución")
            return True

        self._stop_event.clear()
        self._last_success_ts = 0.0
        self._no_signal_timer = 0.0
        self._emit_state(STATE_CONNECTING)

        self._reader_thread = threading.Thread(
            target=self._reader_loop,
            name="HDMI-Capture-Reader",
            daemon=True,
        )
        self._reader_thread.start()
        return True

    def stop(self):
        """Detiene el hilo lector y libera el dispositivo."""
        if not self.is_running() and self._cap is None:
            return

        self._stop_event.set()

        if self._reader_thread is not None:
            self._reader_thread.join(timeout=2.0)
            self._reader_thread = None

        with self._lock:
            if self._cap is not None:
                try:
                    self._cap.release()
                except Exception as exc:
                    logger.debug("Excepción al liberar captura: %s", exc)
                self._cap = None

        self._emit_state(STATE_CLOSED)
        logger.info("HDMI capture detenido")

    # ── Hilo lector ──────────────────────────────────────────────
    def _open_capture(self):
        """Abre el dispositivo de captura con la configuración actual.

        Usa un timeout para no colgarse si OpenCV no responde
        (driver roto, dispositivo ausente, etc.).
        """
        with self._lock:
            if self._cap is not None:
                try:
                    self._cap.release()
                except Exception:
                    pass
                self._cap = None

        result = {"cap": None, "opened": False}
        open_timeout_s = 3.0

        def _do_open():
            cap = cv2.VideoCapture(self._device_index, cv2.CAP_DSHOW)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
                cap.set(cv2.CAP_PROP_FPS, self._fps)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                result["opened"] = True
                result["cap"] = cap
            else:
                try:
                    cap.release()
                except Exception:
                    pass

        t = threading.Thread(target=_do_open, daemon=True)
        t.start()
        t.join(timeout=open_timeout_s)

        if t.is_alive():
            logger.warning(
                "Timeout abriendo dispositivo HDMI %d (OpenCV no responde)",
                self._device_index,
            )
            return False

        if not result["opened"] or result["cap"] is None:
            return False

        with self._lock:
            self._cap = result["cap"]
        return True

    def _reader_loop(self):
        """Bucle principal: abre el dispositivo, lee frames, emite signals."""
        if not self._open_capture():
            logger.error("No se pudo abrir dispositivo HDMI %d", self._device_index)
            self._emit_state(STATE_ERROR)
            return

        self._emit_state(STATE_CONNECTED)

        try:
            while not self._stop_event.is_set():
                loop_start = time.monotonic()

                cap = None
                with self._lock:
                    cap = self._cap

                if cap is None:
                    self._emit_state(STATE_ERROR)
                    break

                # cap.read() puede bloquearse en drivers rotos; lo ejecutamos
                # en un subproceso con timeout para no congelar el hilo lector.
                read_result = {"ok": False, "frame": None}
                read_timeout_s = max(1.0, self._frame_interval * 2.0)

                def _do_read():
                    try:
                        ok, frame = cap.read()
                        read_result["ok"] = ok
                        read_result["frame"] = frame
                    except Exception as exc:
                        logger.debug("Excepción en cap.read(): %s", exc)

                rt = threading.Thread(target=_do_read, daemon=True)
                rt.start()
                rt.join(timeout=read_timeout_s)

                if rt.is_alive():
                    logger.warning(
                        "Timeout en cap.read() (driver posiblemente colgado)"
                    )
                    if self._state != STATE_NO_SIGNAL:
                        self._emit_state(STATE_NO_SIGNAL)
                    time.sleep(0.1)
                    continue

                if not read_result["ok"] or read_result["frame"] is None:
                    now = time.monotonic()
                    if self._no_signal_timer == 0.0:
                        self._no_signal_timer = now
                    elif (now - self._no_signal_timer) >= _NO_SIGNAL_TIMEOUT_S:
                        if self._state != STATE_NO_SIGNAL:
                            logger.warning("HDMI sin señal (>%.1fs)", _NO_SIGNAL_TIMEOUT_S)
                            self._emit_state(STATE_NO_SIGNAL)
                    time.sleep(0.1)
                    continue

                self._no_signal_timer = 0.0
                if self._state == STATE_NO_SIGNAL:
                    logger.info("HDMI señal recuperada")
                    self._emit_state(STATE_CONNECTED)

                img = self._frame_to_qimage(read_result["frame"])
                if img is not None:
                    self.frame_ready.emit(img)

                elapsed = time.monotonic() - loop_start
                sleep_s = self._frame_interval - elapsed
                if sleep_s > 0:
                    time.sleep(sleep_s)

        except Exception as exc:
            logger.error("Error en hilo lector HDMI: %s", exc, exc_info=True)
            self._emit_state(STATE_ERROR)
        finally:
            with self._lock:
                if self._cap is not None:
                    try:
                        self._cap.release()
                    except Exception:
                        pass
                    self._cap = None

    @staticmethod
    def _frame_to_qimage(frame) -> 'QImage | None':
        """Convierte un frame BGR de OpenCV a QImage RGB888."""
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            bytes_per_line = ch * w
            return QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).copy()
        except Exception as exc:
            logger.debug("Error convirtiendo frame a QImage: %s", exc)
            return None

    # ── Helpers ──────────────────────────────────────────────────
    def _emit_state(self, new_state: str):
        if new_state != self._state:
            logger.debug("HDMI state: %s -> %s", self._state, new_state)
            self._state = new_state
            self.state_changed.emit(new_state)


def get_capture_manager() -> HDMICaptureManager:
    """Devuelve el singleton del capturador HDMI."""
    return HDMICaptureManager.instance()