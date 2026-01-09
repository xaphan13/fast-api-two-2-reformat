from app22.db_crud_base.async_crud_base import AsyncBaseCRUD
from app22.core.templates_model import TableName
from app22.core.templates_schema import Create, Get


class TemplatesAsyncCRUD(AsyncBaseCRUD[TableName, Create, Get, Create, Get]):
    def get_model(self):
        return self.model


templatesDB = TemplatesAsyncCRUD(TableName)
