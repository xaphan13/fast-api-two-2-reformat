from typing import Optional, List
from pydantic import BaseModel
from enum import Enum
from datetime import datetime


# ==============================================================================
# ++++++++++++++++++ BaseModel - JoinPerson - pydantic +++++++++++++++++++++++++
# ------------------------------------------------------------------------------
class GetJoinPerson(BaseModel):
    id: Optional[int] = None
    time_created: Optional[datetime] = None
    name: Optional[str] = None
    surname: Optional[str] = None
    link_addr: Optional[int] = None


class CreateJoinPerson(BaseModel):
    name: str
    surname: str
    link_addr: Optional[int] = None


class OrderbyJoinPersonEnum(str, Enum):
    id: str = "id"
    time_created: str = "time_created"
    name: str = "name"
    surname: str = "surname"
    link_addr: int = "link_addr"


class OrderbyJoinPersonList(BaseModel):
    order_by_list: List[OrderbyJoinPersonEnum] = ["id"]


class RespJoinPerson(BaseModel):
    id: Optional[int]
    time_created: Optional[datetime]
    name: Optional[str]
    surname: Optional[str]
    link_addr: Optional[int]


# ==============================================================================
# ++++++++++++++++++ BaseModel - JoinAddress - pydantic ++++++++++++++++++++++++
# ------------------------------------------------------------------------------
class GetJoinAddress(BaseModel):
    id: Optional[int] = None
    time_created: Optional[datetime] = None
    city: Optional[str] = None
    street: Optional[str] = None
    addr_index: Optional[int] = None


class CreateJoinAddress(BaseModel):
    city: str
    street: str
    addr_index: int


class OrderbyJoinAddressEnum(str, Enum):
    id: str = "id"
    time_created: str = "time_created"
    city: str = "city"
    street: str = "street"
    addr_index: int = "addr_index"


class OrderbyJoinAddressList(BaseModel):
    order_by_list: List[OrderbyJoinAddressEnum] = ["id"]


class RespJoinAddress(BaseModel):
    id: Optional[int]
    time_created: Optional[datetime]
    city: Optional[str]
    street: Optional[str]
    addr_index: Optional[int]
