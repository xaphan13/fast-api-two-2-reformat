from pydantic import BaseModel, Field

from typing import Optional, List, Self

from enum import Enum

from app22.async_reader_project.schema_reader import (
    SchemaListBook,
    SchemaReader,
    SchemaCategory,
    SchemaBook,
)

from app22.async_reader_project.model_reader_book import Reader, Book


# ==============================================================================
# +++++++++++++++ ListBookAssociation - "list_book_association" ++++++++++++++++
# ------------------------------------------------------------------------------
class QtyBookReader(BaseModel):
    qty_all: Optional[int] = None
    book: Optional[SchemaBook] = None
    readers: List[SchemaReader] = []

    def set_book(self, book: Book) -> Self:
        self.book = SchemaBook.model_validate(book)
        return self

    def append_reader(self, reader: Reader) -> Self:
        self.readers.append(SchemaReader.model_validate(reader))
        return self


# ==============================================================================
# +++++++++++++++++++++++ Reader - Add Books - ListBook ++++++++++++++++++++++++
# ------------------------------------------------------------------------------
class SchemaAddBook(BaseModel):
    reader_id: Optional[int] = None
    reader_nickname: Optional[str] = None
    list_id: Optional[int] = None
    list_name: Optional[str] = None


class ReaderAddBooks(BaseModel):
    id: Optional[int] = Field(None, alias="reader_id")
    nickname: Optional[str] = Field(None, alias="reader_nickname")


class ListBookAddBooks(BaseModel):
    id: Optional[int] = Field(None, alias="list_id")
    list_name: Optional[str] = Field(None, alias="list_name")


# ==============================================================================
# ++++++++++++++++++ SchemaDeleteId - all tables READER-PRO ++++++++++++++++++++
# ------------------------------------------------------------------------------
class DeleteEnum(str, Enum):
    reader = "reader"
    list = "list"
    book = "book"
    category = "category"


class SchemaDeleteId(BaseModel):
    id: Optional[int] = 0
    type_del: DeleteEnum


# ==============================================================================
# ++++++++++ ListBook - relationship - SchemaReader and SchemaBook +++++++++++++
# ------------------------------------------------------------------------------
class ListBookReader(SchemaListBook):
    reader: SchemaReader


class ListBookReaderBooks(SchemaListBook):
    books: List[SchemaBook]
    reader: SchemaReader


class ListBookWithBooks(SchemaListBook):
    books: Optional[List[SchemaBook]] = []


# ==============================================================================
# ++++++++++++++++++ SchemaReader - relationship - ListBook ++++++++++++++++++++
# ------------------------------------------------------------------------------
class ReaderLists(SchemaReader):
    book_lists: Optional[List[SchemaListBook]] = []


class ReaderListsBooks(SchemaReader):
    book_lists: Optional[List[ListBookWithBooks]] = []


# ==============================================================================
# ++++++++++++++++++++ Book - relationship - SchemaBook ++++++++++++++++++++++++
# ------------------------------------------------------------------------------
class SchemaBookWithCategory(SchemaBook):
    categories: List[SchemaCategory]


class SchemaBookWithLists(SchemaBook):
    lists: List[SchemaListBook]


class SchemaBookWithCategoryLists(SchemaBook):
    categories: List[SchemaCategory]
    lists: List[SchemaListBook]


class GetBookRelEnum(str, Enum):
    lists = "lists"
    categories = "categories"
    all = "all"
    one = "one"


class SchemaGetBookRel(BaseModel):
    select: GetBookRelEnum


# ==============================================================================
# ++++++++++++ UploadFile upload_file + download_file FileResponse +++++++++++++
# ------------------------------------------------------------------------------
class DownloadFileReq(BaseModel):
    file_name: str
    dir_name: Optional[str] = None


class UploadFileReq(BaseModel):
    file_name: Optional[str] = None
    dir_name: Optional[str] = None
