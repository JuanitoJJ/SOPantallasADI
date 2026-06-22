import os
import sys
import threading
import time
import traceback
from datetime import datetime
from core.logger import get_logger


logger = get_logger("core.watchdog")


WATCHDOG_MARKER_FILE = ".watchdog_alive"
HEARTBEAT_INTERVAL = 30
WATCHDOG_TIMEOUT = 90


class CrashHandler:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._heartbeat_thread = None
        self._stop_event = threading.Event()
        self._restart_callback = None
        self._watcher_thread = None
        self._excepthook_installed = False

    def install(self, restart_callback=None):
        if self._excepthook_installed:
            return
        self._restart_callback = restart_callback
        sys.excepthook = self._exception_hook
        threading.excepthook = self._thread_exception_hook
        self._excepthook_installed = True
        logger.info("CrashHandler instalado")

    def start_heartbeat(self):
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            return
        self._stop_event.clear()
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop, daemon=True, name="WatchdogHeartbeat"
        )
        self._heartbeat_thread.start()

    def stop_heartbeat(self):
        self._stop_event.set()
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=2.0)
        try:
            if os.path.exists(WATCHDOG_MARKER_FILE):
                os.remove(WATCHDOG_MARKER_FILE)
        except Exception:
            pass

    def _heartbeat_loop(self):
        while not self._stop_event.is_set():
            try:
                with open(WATCHDOG_MARKER_FILE, "w", encoding="utf-8") as f:
                    f.write(datetime.now().isoformat())
            except Exception as exc:
                logger.warning("No se pudo escribir heartbeat: %s", exc)
            self._stop_event.wait(HEARTBEAT_INTERVAL)

    def _exception_hook(self, exc_type, exc_value, exc_tb):
        logger.critical("Excepción no capturada en hilo principal:")
        logger.critical("".join(traceback.format_exception(exc_type, exc_value, exc_tb)))
        self._handle_crash()

    def _thread_exception_hook(self, args):
        logger.critical("Excepción no capturada en hilo %s:", args.thread.name)
        logger.critical("".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback)))
        self._handle_crash()

    def _handle_crash(self):
        if self._restart_callback:
            try:
                logger.info("Ejecutando callback de recuperación antes de salir")
                self._restart_callback()
            except Exception as exc:
                logger.error("Callback de recuperación falló: %s", exc)
        self.stop_heartbeat()
        if self._restart_callback:
            self._restart_process()
        sys.exit(1)

    def _restart_process(self):
        try:
            logger.info("Reiniciando proceso principal")
            python = sys.executable
            args = [python] + sys.argv
            if getattr(sys, "frozen", False):
                os.execv(sys.executable, sys.argv)
            else:
                os.execv(python, args)
        except Exception as exc:
            logger.error("No se pudo reiniciar el proceso: %s", exc)


class WatchdogProcess:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._stop_event = threading.Event()
        self._watcher_thread = None

    def start(self):
        if self._watcher_thread and self._watcher_thread.is_alive():
            return
        self._stop_event.clear()
        self._watcher_thread = threading.Thread(
            target=self._watch_loop, daemon=True, name="WatchdogMonitor"
        )
        self._watcher_thread.start()
        logger.info("Watchdog monitor iniciado (timeout=%ds)", WATCHDOG_TIMEOUT)

    def stop(self):
        self._stop_event.set()
        if self._watcher_thread and self._watcher_thread.is_alive():
            self._watcher_thread.join(timeout=2.0)

    def _watch_loop(self):
        while not self._stop_event.is_set():
            if not os.path.exists(WATCHDOG_MARKER_FILE):
                self._stop_event.wait(10)
                continue

            try:
                mtime = os.path.getmtime(WATCHDOG_MARKER_FILE)
                age = time.time() - mtime
                if age > WATCHDOG_TIMEOUT:
                    logger.error(
                        "Aplicación colgada detectada (heartbeat %.0fs). Reiniciando...",
                        age,
                    )
                    self._restart_app()
                    return
            except OSError:
                pass
            self._stop_event.wait(HEARTBEAT_INTERVAL)

    def _restart_app(self):
        try:
            if getattr(sys, "frozen", False):
                os.execv(sys.executable, sys.argv)
            else:
                os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as exc:
            logger.error("Watchdog no pudo reiniciar: %s", exc)


crash_handler = CrashHandler()
watchdog = WatchdogProcess()
