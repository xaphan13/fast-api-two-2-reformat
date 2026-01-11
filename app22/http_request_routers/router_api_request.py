from fastapi import APIRouter, HTTPException

from datetime import datetime, timezone

from app22.http_request_routers.Class_client_https import (
    RespServer,
)
from app22.http_request_routers.client_openweathermap import (
    main_weather_create_task,
    main_weather_await,
    WeatherBodyReq,
)

from app22.config_log import ConfigLogger

logFC = ConfigLogger.get_logger("FileStdout")


api_request = APIRouter(
    prefix="/api_request",
    tags=["api_request aiohttp ClientSession"],
)


@api_request.post("/weather_create_task", response_model=RespServer)
async def weather_create_task(body: WeatherBodyReq):
    logFC.info(f"POST/weather_create_task : {datetime.now(timezone.utc)} : \n{body.model_dump()}")

    result: RespServer = await main_weather_create_task(body.q, body.APPID)

    logFC.info(f"POST/weather_create_task : {datetime.now(timezone.utc)} : res \n{result}")

    if result is None:
        raise HTTPException(status_code=500, detail="Task 'weather_create_task' execution failed")
    return result


@api_request.post("/weather_await_response", response_model=RespServer)
async def weather_await_response(body: WeatherBodyReq):
    logFC.info(f"POST/weather_await_response : {datetime.now(timezone.utc)} : \n{body.model_dump()}")

    result: RespServer = await main_weather_await(body.q, body.APPID)

    logFC.info(f"POST/weather_await_response : {datetime.now(timezone.utc)} : res \n{result}")

    if result is None:
        raise HTTPException(status_code=500, detail="Task 'weather_await_response' execution failed")
    return result
