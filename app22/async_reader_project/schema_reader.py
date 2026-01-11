from pydantic import BaseModel

from typing import Optional, List, Self

from datetime import datetime
from enum import Enum


# ==============================================================================
# +++++++++++++++++++++ Reader - "readers" - SchemaReader ++++++++++++++++++++++
# ------------------------------------------------------------------------------
class SchemaReader(BaseModel):
    id: Optional[int] = None
    nickname: Optional[str] = None
    user_id: Optional[int] = None

    class Config:
        from_attributes = True


class CreateReader(BaseModel):
    nickname: str
    user_id: Optional[int] = None


class ReaderEnum(str, Enum):
    id = "id"
    nickname = "nickname"
    user_id = "user_id"


class OrderbyReader(BaseModel):
    order_by_list: List[ReaderEnum] = ["id"]


# ==============================================================================
# ++++++++++++++++++ ListBook - "listbooks" - SchemaListBook +++++++++++++++++++
# ------------------------------------------------------------------------------
class SchemaListBook(BaseModel):
    id: Optional[int] = None
    time_created: Optional[datetime] = None
    list_name: Optional[str] = None
    description: Optional[str] = None
    reader_id: Optional[int] = None


class CreateListBook(BaseModel):
    list_name: str
    description: str
    reader_id: Optional[int] = None

    def set_reader(self, reader_id: int) -> Self:
        self.reader_id = reader_id
        return self


class ListBookEnum(str, Enum):
    id = "id"
    time_created = "time_created"
    list_name = "list_name"
    description = "description"


class OrderbyListBook(BaseModel):
    order_by_list: List[ListBookEnum] = ["id"]


# ==============================================================================
# ++++++++++++++++++++++ Book - "books" - SchemaBook ++++++++++++++++++++++++++
# ------------------------------------------------------------------------------
class SchemaBook(BaseModel):
    id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None

    class Config:
        from_attributes = True


class CreateBook(BaseModel):
    title: str
    description: str
    author: str


class BookEnum(str, Enum):
    id = "id"
    title = "title"
    description = "description"
    author = "author"


class ListOrderbyBook(BaseModel):
    order_by_list: List[BookEnum] = ["id"]


class OrderbyBook(BaseModel):
    order_by: BookEnum = "id"


# ==============================================================================
# +++++++++++++++++++ Category - "categories" - SchemaCategory +++++++++++++++++
# ------------------------------------------------------------------------------
class SchemaCategory(BaseModel):
    id: Optional[int] = None
    genre: Optional[str] = None
    description: Optional[str] = None


class CreateCategory(BaseModel):
    genre: str
    description: str


class CategoryEnum(str, Enum):
    id = "id"
    genre = "genre"
    description = "description"


class OrderbyCategory(BaseModel):
    order_by_list: List[CategoryEnum] = ["id"]
