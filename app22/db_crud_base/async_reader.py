from app22.db_crud_base.async_crud_base import AsyncBaseCRUD, SqlType, ReaderType, CreateType
from app22.async_reader_project.model_reader_book import Reader, ListBook, Book, Category
from app22.async_reader_project.schema_reader import (
    CreateReader,
    SchemaReader,
    SchemaListBook,
    CreateListBook,
    CreateBook,
    SchemaBook,
    SchemaCategory,
    CreateCategory,
)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import select


# ==============================================================================
# ++++++++++++++++++ Reader - ReaderAsyncCRUD - SchemaReader +++++++++++++++++++
# ------------------------------------------------------------------------------
class ReaderAsyncCRUD(AsyncBaseCRUD[Reader, CreateReader, SchemaReader, SchemaReader, SchemaReader]):
    async def get_reader_bookL_one(self, schema: ReaderType, db: AsyncSession) -> SqlType | None:
        query = select(self.model).where(*self._get_filter_attr(schema)).options(selectinload(self.model.book_lists))
        return await self.get_record_one(schema, db, query_n=query)


readerDB = ReaderAsyncCRUD(Reader)


# ==============================================================================
# ++++++++++++++++++ ListBook - ListBookAsyncCRUD - SchemaListBook +++++++++++++++++++
# ------------------------------------------------------------------------------
class ListBookAsyncCRUD(AsyncBaseCRUD[ListBook, CreateListBook, SchemaListBook, SchemaListBook, SchemaListBook]):
    def get_model(self):
        return self.model


listbookDB = ListBookAsyncCRUD(ListBook)


# ==============================================================================
# ++++++++++++++++++ Book - BookAsyncCRUD - SchemaBook +++++++++++++++++++
# ------------------------------------------------------------------------------
class BookAsyncCRUD(AsyncBaseCRUD[Book, CreateBook, SchemaBook, SchemaBook, SchemaBook]):
    async def add_book_to_list(
        self, schema: CreateType, db: AsyncSession, listBooks: ListBook = None, commit: bool = True
    ) -> SqlType:
        new_record = self.model(**schema.model_dump())
        if listBooks is not None:
            new_record.lists.append(listBooks)
        db.add(new_record)
        if commit:
            await db.commit()
            await db.refresh(new_record)
        return new_record


bookDB = BookAsyncCRUD(Book)  # joinedload


# ==============================================================================
# ++++++++++++++++++ Category - CategoryAsyncCRUD - SchemaCategory +++++++++++++++++++
# ------------------------------------------------------------------------------
class CategoryAsyncCRUD(AsyncBaseCRUD[Category, CreateCategory, SchemaCategory, SchemaCategory, SchemaCategory]):
    def get_model(self):
        return self.model


categoryDB = CategoryAsyncCRUD(Category)
