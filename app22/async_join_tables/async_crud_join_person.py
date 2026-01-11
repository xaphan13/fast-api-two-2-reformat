from app22.async_join_tables.schema_join import (
    CreateJoinPerson,
    GetJoinPerson,
)

from app22.async_join_tables.model_join import JoinPerson

from app22.db_core.async_crud_base import AsyncBaseCRUD


class AsyncJoinPersonCRUD(AsyncBaseCRUD[JoinPerson, CreateJoinPerson, GetJoinPerson, CreateJoinPerson, GetJoinPerson]):
    def get_model(self):
        return self.model


personDB = AsyncJoinPersonCRUD(JoinPerson)
