import logging
import sys

from src.core.config import settings


def setup_logging(log_level: str | None = None) -> logging.Logger:
    """Configure centralized application logger with secure formatting."""
    level_name = (log_level or settings.LOG_LEVEL).upper()
    level = getattr(logging, level_name, logging.INFO)

    log_format = (
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"

    # Configure root logger
    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    # Specific app logger
    app_logger = logging.getLogger("eldercare")
    app_logger.setLevel(level)

    # Suppress overly verbose third-party loggers if desired
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    return app_logger


# Module-level default logger
logger = setup_logging()
