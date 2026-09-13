import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from app.core.config import settings


def setup_logging():
    """
    Configures centralized logging for AgriKetha-AI backend.
    Supports console output and rotating file logs (app.log & error.log).
    """
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    log_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=log_format, datefmt=date_format)

    # Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Avoid duplicate handlers on re-init
    if root_logger.handlers:
        root_logger.handlers.clear()

    # 1. Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 2. Main App Rotating File Handler (10MB max, 5 backups)
    app_log_path = log_dir / "app.log"
    app_file_handler = RotatingFileHandler(
        filename=str(app_log_path),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    app_file_handler.setLevel(log_level)
    app_file_handler.setFormatter(formatter)
    root_logger.addHandler(app_file_handler)

    # 3. Error Log File Handler (Errors & Critical only)
    error_log_path = log_dir / "error.log"
    error_file_handler = RotatingFileHandler(
        filename=str(error_log_path),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(formatter)
    root_logger.addHandler(error_file_handler)

    # Adjust external noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("motor").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)

    logger = logging.getLogger("agriketha.backend")
    logger.info("Logging initialized successfully. Level: %s", settings.LOG_LEVEL)
    return logger


logger = logging.getLogger("agriketha.backend")
