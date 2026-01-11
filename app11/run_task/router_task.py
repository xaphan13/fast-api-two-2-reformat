from app11.config_log import ConfigLogger
from fastapi import APIRouter, HTTPException, Depends, Query
from starlette.responses import JSONResponse
from celery import Celery
from celery.result import AsyncResult
from datetime import datetime, timedelta
from typing import Union

from app11.run_task.schema_task import ReqTaskSchema, RespTaskSchema
from app11.celery_tasks.celery_worker import depends_celery
from app11.celery_tasks.async_task import create_task, create_shared_task


logFC = ConfigLogger.get_logger("FileStdout")


tasks_route = APIRouter(prefix="/tasks", tags=["Example tasks"])


@tasks_route.post("/task_apply", response_model=RespTaskSchema, status_code=201)
def task_apply(req: ReqTaskSchema):
    amount = int(req.amount)
    x = req.x
    y = req.y

    scheduled_time = datetime.utcnow() + timedelta(seconds=10)
    # task = create_task.apply_async(args=[amount, x, y], countdown=10)
    task: AsyncResult = create_task.apply_async(
        args=[amount, x, y], eta=scheduled_time, retry=True, retry_policy={"max_retries": 3}, priority=5
    )

    logFC.info(f"time = {datetime.utcnow()} - {scheduled_time}")
    task_result = task.get()
    return RespTaskSchema(**req.dict(), result=task_result)


@tasks_route.post("/task_delay", response_model=RespTaskSchema, status_code=201)
def task_delay(req: ReqTaskSchema):
    amount = int(req.amount)
    x = req.x
    y = req.y
    task: AsyncResult = create_task.delay(amount, x, y)

    task_result = task.get()
    logFC.info(f"time = {datetime.utcnow()} - POST/task_delay = {task_result}")

    if task_result is None:
        raise HTTPException(status_code=500, detail="Task 'create_task.delay' execution failed")

    return RespTaskSchema(**req.dict(), result=task_result)


@tasks_route.post("/shared_task", response_model=RespTaskSchema)
def shared_task(req: ReqTaskSchema):
    amount = int(req.amount)
    x = req.x
    y = req.y
    task: AsyncResult = create_shared_task.delay(amount, x, y)
    logFC.info(f"task = {task.id} - {task.task_id} - {task.status}")

    task_get = task.get()
    if task_get is None:
        raise HTTPException(status_code=500, detail="Task 'shared_task.delay' execution failed")
    return JSONResponse({**req.dict(exclude={"amount"}), "result": task_get})


task_id: Union[None, str] = None


@tasks_route.get("/send_task")
def send_task(
    a: int = Query(30, ge=1, le=99),
    b: int = Query(40, ge=1, le=99),
    work_sleep: int = Query(2, ge=1, le=9, description="time.sleep(sec)"),
    delay_exec_sec: int = Query(30, ge=1, le=3600, description="eta=scheduled_time"),
    celery: Celery = Depends(depends_celery),
):
    global task_id
    if task_id is not None:
        raise HTTPException(status_code=404, detail="Task started - only one task")

    scheduled_time = datetime.utcnow() + timedelta(seconds=delay_exec_sec)

    task_result: AsyncResult = celery.send_task("create_task", args=[work_sleep, a, b], eta=scheduled_time)

    task_id = task_result.id
    return {"task_id": task_result.id}  # return {"task_result": task_result.get()}


@tasks_route.get("/check_send_task")
def check_send_task():
    global task_id
    if task_id is None:
        raise HTTPException(status_code=405, detail="Task not started")

    task = AsyncResult(task_id)

    if task.status == "SUCCESS":
        result = task.get()
        logFC.info(f"task.get() after SUCCESS = {result}")
        task_id = None
        return {"task.get": result}
    elif task.status == "PENDING":
        logFC.info("task.status == PENDING")
        return {"task.status": "PENDING"}
    elif task.status == "STARTED":
        logFC.info("task.status == STARTED")
        return {"task.status": "STARTED"}
    elif task.status == "FAILURE":
        logFC.info("task.status == FAILURE")
        return {"task.status": "FAILURE"}
