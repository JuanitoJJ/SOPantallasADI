import logging
import logging.handlers
import os
from datetime import datetime
from core.path_utils import get_resource_path


LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_DIR = "logs"
LOG_FILE = "sopantallas.log"
MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 5


_initialized = False


def _ensure_log_dir():
    log_dir = get_resource_path(LOG_DIR)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    return log_dir


def get_logger(name: str) -> logging.Logger:
    global _initialized
    logger = logging.getLogger(name)

    if _initialized:
        return logger

    root_logger = logging.getLogger()
    if root_logger.handlers:
        _initialized = True
        return logger

    root_logger.setLevel(logging.INFO)
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)

    log_dir = _ensure_log_dir()
    log_path = os.path.join(log_dir, LOG_FILE)
    file_handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    _initialized = True

    logger.info("=" * 60)
    logger.info("SOPantallasADI iniciando — %s", datetime.now().strftime(DATE_FORMAT))
    logger.info("=" * 60)

    return logger


def log_event(category: str, message: str, level: int = logging.INFO):
    logger = get_logger(f"sopantallas.{category}")
    logger.log(level, message)
