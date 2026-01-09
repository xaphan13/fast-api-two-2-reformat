from pydantic import BaseModel

from app22.config_log import ConfigLogger
from fastapi import APIRouter, HTTPException
from datetime import datetime

from app22.http_request_routers.Class_client_https import (
    RespServer,
    main_weather_create_task,
    main_weather_await,
)


logFC = ConfigLogger.get_logger("FileStdout", "api_request")


api_request = APIRouter(prefix="/api_request", tags=["NEW api_request"])


class WeatherBodyReq(BaseModel):
    q: str = "Moscow"
    APPID: str = "2a4ff86f9aaa70041ec8e82db64abf56"


@api_request.post("/weather_create_task", response_model=RespServer)
async def weather_create_task(body: WeatherBodyReq):
    logFC.info(f"POST/weather_create_task : {datetime.utcnow()} : \n{body.dict()}")

    result: RespServer = await main_weather_create_task(body.q, body.APPID)

    logFC.info(f"POST/weather_create_task : {datetime.utcnow()} : res \n{result}")

    if result is None:
        raise HTTPException(status_code=500, detail="Task 'weather_create_task' execution failed")
    return result


@api_request.post("/weather_await_response", response_model=RespServer)
async def weather_await_response(body: WeatherBodyReq):
    logFC.info(f"POST/weather_await_response : {datetime.utcnow()} : \n{body.dict()}")

    result: RespServer = await main_weather_await(body.q, body.APPID)

    logFC.info(f"POST/weather_await_response : {datetime.utcnow()} : res \n{result}")

    if result is None:
        raise HTTPException(status_code=500, detail="Task 'weather_await_response' execution failed")
    return result
