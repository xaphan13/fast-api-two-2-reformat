from app22.db_core.async_crud_base import AsyncBaseCRUD
from app22.template_files.templates_model import TableName
from app22.template_files.templates_schema import Create, Get


class TemplatesAsyncCRUD(
    AsyncBaseCRUD[
        TableName,
        Create,
        Get,
        Create,
        Get,
    ]
):
    def get_model(self):
        return self.model


templatesDB = TemplatesAsyncCRUD(TableName)
