from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from enum import Enum


# ==============================================================================
# +++++++++++++++ ListBookAssociation - "list_book_association" ++++++++++++++++
# ------------------------------------------------------------------------------
class SchemaListBookAssociation(BaseModel):
    id: Optional[int] = None
    time_add: Optional[datetime] = None
    list_id: Optional[int] = None
    book_id: Optional[int] = None


class CreateListBookAssociation(BaseModel):
    list_id: int
    book_id: int


class ListBookAssociationEnum(str, Enum):
    id: str = "id"
    time_add: str = "time_add"
    list_id: str = "list_id"
    book_id: str = "book_id"


class OrderbyListBookAssociation(BaseModel):
    order_by_list: List[ListBookAssociationEnum] = ["id"]


# ==============================================================================
# +++++++++++ BookCategoryAssociation - "book_category_association" ++++++++++++
# ------------------------------------------------------------------------------
class SchemaBookCategoryAssociation(BaseModel):
    id: Optional[int] = None
    book_id: Optional[int] = None
    category_id: Optional[int] = None


class CreateBookCategoryAssociation(BaseModel):
    book_id: int
    category_id: int


class BookCategoryAssociationEnum(str, Enum):
    id: str = "id"
    book_id: str = "book_id"
    category_id: str = "category_id"


class OrderbyBookCategoryAssociation(BaseModel):
    order_by_list: List[BookCategoryAssociationEnum] = ["id"]
