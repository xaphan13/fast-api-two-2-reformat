from typing import Optional, List
from pydantic import BaseModel
from enum import Enum
from datetime import datetime


# ***************************************************************************************
# QUERY : JoinPerson =================================================
# ---------------------------------------------------------------------------------------
class Get(BaseModel):
    id: Optional[int] = None
    time_created: Optional[datetime] = None
    name: Optional[str] = None
    surname: Optional[str] = None
    addr_id: Optional[int] = None


class Create(BaseModel):
    name: str
    surname: str
    addr_id: int


class OrderbyEnum(str, Enum):
    id: str = "id"
    time_created: str = "time_created"
    name: str = "name"
    surname: str = "surname"
    addr_id: int = "addr_id"


class OrderbyList(BaseModel):
    order_by_list: List[OrderbyEnum] = ["id"]


class Resp(BaseModel):
    id: Optional[int]
    time_created: Optional[datetime]
    name: Optional[str]
    surname: Optional[str]
    addr_id: Optional[int]
