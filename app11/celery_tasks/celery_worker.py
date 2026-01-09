from celery import Celery

from app11.core.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND


celery = Celery("celery_worker_new", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)


celery.conf.update(
    task_serializer="json",
    accept_content=["json"],  # Ignore other content
    result_serializer="json",
    enable_utc=True,
    include=["celery_tasks.async_task", "celery_tasks.temp_task"],
)


def depends_celery() -> Celery:
    return celery
