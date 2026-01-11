from pydantic import BaseModel

from typing import Optional, List

from datetime import datetime
from enum import Enum


# ==============================================================================
# ++++++++++++++++++++++ BaseModel - User - pydantic +++++++++++++++++++++++++++
# ------------------------------------------------------------------------------
class GetUser(BaseModel):
    id: Optional[int] = None
    nickname: Optional[str] = None
    email: Optional[str] = None
    firstname: Optional[str] = None
    surname: Optional[str] = None
    password: Optional[str] = None


class CreateUser(BaseModel):
    nickname: str
    email: str
    firstname: Optional[str] = None
    surname: Optional[str] = None
    password: str


class OrderbyUserEnum(str, Enum):
    id = "id"
    nickname = "nickname"
    email = "email"
    firstname = "firstname"
    surname = "surname"


class OrderbyUserList(BaseModel):
    order_by_list: List[OrderbyUserEnum] = ["id"]


class RespUser(BaseModel):
    id: Optional[int]
    nickname: Optional[str]
    email: Optional[str]
    firstname: Optional[str]
    surname: Optional[str]
    password: Optional[str]


# ==============================================================================
# ++++++++++++++++++++++ BaseModel - Post - pydantic +++++++++++++++++++++++++++
# ------------------------------------------------------------------------------
class GetPost(BaseModel):
    id: Optional[int] = None
    time_created: Optional[datetime] = None
    title: Optional[str] = None
    content: Optional[str] = None
    user_id: Optional[int] = None


class CreatePost(BaseModel):
    title: str
    content: str
    user_id: Optional[int] = None


class OrderbyPostEnum(str, Enum):
    id = "id"
    time_created = "time_created"
    title = "title"
    content = "content"
    user_id = "user_id"


class OrderbyPostList(BaseModel):
    order_by_list: List[OrderbyPostEnum] = ["id"]


class RespPost(BaseModel):
    id: Optional[int]
    time_created: Optional[datetime]
    title: Optional[str]
    content: Optional[str]
    user_id: Optional[int]
