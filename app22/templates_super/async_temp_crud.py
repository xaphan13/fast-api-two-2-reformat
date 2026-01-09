from app22.db_core.model.model_reader_book import Reader, ListBook, Book, Category

from app22.reader_project.schema_reader import (
    CreateReader,
    SchemaReader,
    SchemaListBook,
    CreateListBook,
    CreateBook,
    SchemaBook,
    SchemaCategory,
    CreateCategory,
)

from app22.db_crud_base.async_crud_base import AsyncBaseCRUD


# ==============================================================================
# ++++++++++++++++++ Reader - ReaderAsyncCRUD - SchemaReader +++++++++++++++++++
# ------------------------------------------------------------------------------
class ReaderAsyncCRUD(AsyncBaseCRUD[Reader, CreateReader, SchemaReader, SchemaReader, SchemaReader]):
    def get_model(self):
        return self.model


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
    def get_model(self):
        return self.model


bookDB = BookAsyncCRUD(Book)


# ==============================================================================
# ++++++++++++++++++ Category - CategoryAsyncCRUD - SchemaCategory +++++++++++++++++++
# ------------------------------------------------------------------------------
class CategoryAsyncCRUD(AsyncBaseCRUD[Category, CreateCategory, SchemaCategory, SchemaCategory, SchemaCategory]):
    def get_model(self):
        return self.model


categoryDB = CategoryAsyncCRUD(Category)
