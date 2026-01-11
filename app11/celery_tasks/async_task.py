from app11.config_log import ConfigLogger
from celery import shared_task
from datetime import datetime
import time

from app11.celery_tasks.celery_worker import celery


logFC = ConfigLogger.get_logger("FileStdout")


@celery.task(name="create_task")
def create_task(a, b, c):
    logFC.info(f"'Celery' {datetime.utcnow()}: celery.task - before : {a} + {b} = {c}")
    time.sleep(a)
    logFC.info(f"'Celery' {datetime.utcnow()}: celery.task - after : {a} + {b} = {c}")
    return b + c + 3


@shared_task(name="create_shared_task")
def create_shared_task(a, b, c):
    logFC.info(f"'Celery' {datetime.utcnow()}: shared_task - before : {a} + {b} = {c}")
    time.sleep(a)
    logFC.info(f"'Celery' {datetime.utcnow()}: shared_task - after : {a} + {b} = {c}")
    return b + c + 4
