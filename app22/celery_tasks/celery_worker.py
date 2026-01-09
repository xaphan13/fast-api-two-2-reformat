from celery import Celery

from app22.core.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND


celery = Celery("celery_two_new", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)


celery.conf.update(
    task_serializer="json",
    accept_content=["json"],  # Ignore other content
    result_serializer="json",
    enable_utc=True,
    include=["celery_tasks.new_tasks"],
)


def depends_celery() -> Celery:
    return celery
