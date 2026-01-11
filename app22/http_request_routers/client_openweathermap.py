from _asyncio import Task
from pydantic import BaseModel

from app22.http_request_routers.Class_client_https import ClientHTTPS, RespServer


# ****************************************************
# template await response - send request ClientHTTPS #
# ****************************************************
client_weather: ClientHTTPS = ClientHTTPS("api.openweathermap.org", True)


class WeatherBodyReq(BaseModel):
    q: str = "Moscow"
    APPID: str = "2a4ff86f9aaa70041ec8e82db64abf56"


# ********************************************************* asyncio.create_task
def weather_response_call(task: Task[RespServer]):
    result: RespServer = task.result()
    return result


async def main_weather_create_task(city: str, appid: str) -> RespServer:
    path = "/data/2.5/weather"
    params = {"q": city, "APPID": appid}
    task1: Task[RespServer] = client_weather.get_req_create(
        path,
        params=params,
        callback=weather_response_call,
    )
    result: RespServer = await task1

    return result


# ********************************************************* await session.get
async def main_weather_await(city: str, appid: str) -> RespServer:
    path = "/data/2.5/weather"
    params = {"q": city, "APPID": appid}
    result: RespServer = await client_weather.get_req_await(
        path,
        params=params,
    )

    return result
