from pydantic import BaseModel
from datetime import datetime


# **************************************************************
class TaskOneAdd(BaseModel):
    title: str
    msg: str


class TaskOneQuery(BaseModel):
    id: int
    title: str
    msg: str
    time_created: datetime


# **************************************************************
class ReqTaskSchema(BaseModel):
    amount: int
    x: int
    y: int


class RespTaskSchema(BaseModel):
    x: int
    y: int
    result: int


# **************************************************************
class Req1BodyReq(BaseModel):
    sleep_sec: int = 1


class Req1ParamsReq(BaseModel):
    q: str = "Moscow"
    APPID: str = "2a4ff86f9aaa70041ec8e82db64abf56"


class ResponseReq1(BaseModel):
    sleep_sec: int
    result: dict


# **************************************************************
class WeatherBodyReq(BaseModel):
    q: str = "Moscow"
    APPID: str = "2a4ff86f9aaa70041ec8e82db64abf56"
