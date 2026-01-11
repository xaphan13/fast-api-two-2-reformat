from app22.async_join_tables.schema_join import (
    CreateJoinAddress,
    GetJoinAddress,
)

from app22.async_join_tables.model_join import JoinAddress

from app22.db_core.async_crud_base import AsyncBaseCRUD


class AsyncJoinAddressCRUD(
    AsyncBaseCRUD[JoinAddress, CreateJoinAddress, GetJoinAddress, CreateJoinAddress, GetJoinAddress]
):
    def get_model(self):
        return self.model


addrDB = AsyncJoinAddressCRUD(JoinAddress)
