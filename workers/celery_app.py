from celery import Celery

from common.config import settings
from common.logging import configure_logging

configure_logging()

celery_app = Celery(
    "presidio_sit",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
