import logging
import sys

from pythonjsonlogger import jsonlogger

from common.config import settings


def configure_logging() -> None:
    """Configure structured JSON logging."""

    logger = logging.getLogger()
    logger.setLevel(settings.log_level)
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    handler.setFormatter(formatter)
    logger.handlers = [handler]
