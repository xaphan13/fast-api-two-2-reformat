from app22.logger_core.config_logger import ConfigLogger
import asyncio
from asyncio import Task
from aiohttp import ClientSession
from pydantic import BaseModel
from typing import Callable, Optional


logFC = ConfigLogger.getLogger("FileStdout", "ClientHTTPS")
logF = ConfigLogger.getLogger("OnlyFile", "ClientHTTPS")


class RespServer(BaseModel):
    response: dict
    url: str
    headers: Optional[dict] = None
    body: Optional[dict] = None

    def get_resp(self) -> dict:
        return self.response

    def get_url_resp(self) -> dict:
        return {"response": self.response, "url": self.url}

    def log_str(self) -> str:
        return f"server -> {self.url}\n    resp -> {self.response}"


# ********************************************************************************************
class ClientHTTPS:
    def __init__(self, server: str, https=True):
        self.server: str = server
        self.protocol: str = "https://" if https else "http://"
        self.headers = {"accept": "application/json", "Content-Type": "application/json"}

    # ------------------------------------------------------------------
    async def get_req_send(self, url: str, headers: dict, params: Optional[dict] = None) -> RespServer:
        paramsR = {} if params is None else params
        async with ClientSession() as session:
            async with session.get(url=url, headers=headers, params=paramsR, verify_ssl=False) as response:
                server_json: dict = await response.json()
                return RespServer(url=str(response.request_info.url), response=server_json)

    # ------------------------------------------------------------------
    async def post_req_send(self, url: str, headers: dict, body: dict, params: Optional[dict] = None) -> RespServer:
        paramsR = {} if params is None else params
        async with ClientSession() as session:
            async with session.post(url=url, headers=headers, json=body, params=paramsR, verify_ssl=False) as response:
                server_json: dict = await response.json()
                return RespServer(url=str(response.request_info.url), response=server_json, body=body)

    # ------------------------------------------------------------------
    def get_req_create(
        self, path: str, params: Optional[dict] = None, callback: Optional[Callable] = None
    ) -> Task[RespServer]:
        paramsR = {} if params is None else params
        url = f"{self.protocol}{self.server}{path}"
        task: Task[RespServer] = asyncio.create_task(self.get_req_send(url, self.headers, params=paramsR))
        if callback is not None:
            task.add_done_callback(callback)
        return task

    # ------------------------------------------------------------------
    def post_req_create(
        self, path: str, payload: dict, params: Optional[dict] = None, callback: Optional[Callable] = None
    ) -> Task[RespServer]:
        paramsR = {} if params is None else params
        url = f"{self.protocol}{self.server}{path}"
        task: Task[RespServer] = asyncio.create_task(
            self.post_req_send(url, self.headers, body=payload, params=paramsR)
        )
        if callback is not None:
            task.add_done_callback(callback)
        return task

    # ------------------------------------------------------------------
    async def get_req_await(self, path: str, params: Optional[dict] = None) -> RespServer:
        paramsR = {} if params is None else params
        url = f"{self.protocol}{self.server}{path}"
        resp: RespServer = await self.get_req_send(url, self.headers, params=paramsR)
        return resp

    # ------------------------------------------------------------------
    async def post_req_await(self, path: str, payload: dict, params: Optional[dict] = None) -> RespServer:
        paramsR = {} if params is None else params
        url = f"{self.protocol}{self.server}{path}"
        resp: RespServer = await self.post_req_send(url, self.headers, body=payload, params=paramsR)
        return resp


# ********************************************************************************************


api_weather: ClientHTTPS = ClientHTTPS("api.openweathermap.org", True)


# ********************************************************************************************
# template call - send request
# --------------------------------------------------------------------------------------------
# ********************************************************* asyncio.create_task openweathermap
def weather_response_call(task: Task[RespServer]):
    result: RespServer = task.result()


async def main_weather_create_task(city: str, appid: str) -> RespServer:
    path = "/data/2.5/weather"
    params = {"q": city, "APPID": appid}
    task1: Task[RespServer] = api_weather.get_req_create(path, params=params, callback=weather_response_call)
    result: RespServer = await task1
    return result


# ********************************************************* asyncio.create_task openweathermap


# ********************************************************* await openweathermap
async def main_weather_await(city: str, appid: str) -> RespServer:
    path = "/data/2.5/weather"
    params = {"q": city, "APPID": appid}
    result: RespServer = await api_weather.get_req_await(path, params=params)
    return result


# ********************************************************* await openweathermap
