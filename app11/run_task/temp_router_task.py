from app11.config_log import ConfigLogger
from fastapi import APIRouter, HTTPException, Depends
from celery.result import AsyncResult
from datetime import datetime

from app11.celery_tasks.Class_client_https import RespServer
from app11.celery_tasks.temp_task import req1_task, sql_task
from app11.run_task.schema_task import Req1BodyReq, TaskOneAdd, TaskOneQuery, Req1ParamsReq


logFC = ConfigLogger.get_logger("FileStdout")


temp_route = APIRouter(prefix="/temp_route", tags=["Temp tasks"])


@temp_route.post("/req1_delay", response_model=RespServer)
def req1_delay(body: Req1BodyReq, params: Req1ParamsReq = Depends()):
    logFC.info(f"POST/req1_delay : 'start' \n{params.dict()} \n{body.dict()}")
    # result_from_route: RespServer = asyncio.run(main_weather(params.q, params.APPID))
    # logFC.info(f"'CALLBACK req1_delay' = body: {result_from_route.body}\n    {result_from_route.log_str()}")

    task: AsyncResult = req1_task.delay(body.sleep_sec, params.q, params.APPID)

    task_result: dict = task.get()
    result_from_celery: RespServer = RespServer(**task_result)
    logFC.info(f"POST/req1_delay -> 'result_from_celery' - time: {datetime.utcnow()} = {result_from_celery}")

    if task_result is None:
        raise HTTPException(status_code=500, detail="Task 'req1_delay.delay' execution failed")
    return result_from_celery


@temp_route.post("/sql_celery", response_model=TaskOneQuery)
def sql_celery(body: TaskOneAdd):
    logFC.info(f"POST/sql_celery : 'start' - time: {datetime.utcnow()} : body.dict() = {body.dict()}")

    task: AsyncResult = sql_task.delay(body.dict())
    task_result: dict = task.get()

    logFC.info(f"POST/sql_celery - time: {datetime.utcnow()} : task_result = {task_result}")
    if task_result is None:
        raise HTTPException(status_code=500, detail="Task 'sql_celery.delay' execution failed")
    return TaskOneQuery(**task_result)
