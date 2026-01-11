from app11.config_log import ConfigLogger
from fastapi.encoders import jsonable_encoder
from datetime import datetime
import asyncio
import time

from app11.celery_tasks.Class_client_https import main_weather, RespServer
from app11.celery_tasks.celery_worker import celery
from app11.db_core.db_conf import SessionDB
from app11.run_task.model_task import TaskOne
from app11.run_task.schema_task import TaskOneAdd


logFC = ConfigLogger.get_logger("FileStdout")


@celery.task(name="req1_task")
def req1_task(sleep_sec: int = 1, city: str = "", appid: str = ""):
    logFC.info(f"'Celery' {datetime.utcnow()}: req1_task 1 : {sleep_sec} - {city}")

    result: RespServer = asyncio.run(main_weather(city, appid))

    time.sleep(sleep_sec)
    logFC.info(f"'Celery' {datetime.utcnow()}: req1_task 2 : {sleep_sec} - {appid}")
    return result.dict()


@celery.task(name="sql_task")
def sql_task(body_dict: dict):
    logFC.info(f"'Celery' {datetime.utcnow()}: sql_task - 'before' : body_dict = {body_dict}")
    body = TaskOneAdd(**body_dict)

    new_one: TaskOne = TaskOne(title=body.title, msg=body.msg)
    with SessionDB.get_session() as db:
        db.add(new_one)
        db.commit()
        db.refresh(new_one)

    res: dict = jsonable_encoder(new_one)
    logFC.info(f"'Celery' {datetime.utcnow()}: sql_task - 'after' : res = {res}")
    return res
