from app22.db_crud_base.async_crud_base import AsyncBaseCRUD
from app22.db_core.model.model_join import JoinAddress
from app22.join_tables.schema_join import CreateJoinAddress, GetJoinAddress


class AsyncJoinAddressCRUD(
    AsyncBaseCRUD[JoinAddress, CreateJoinAddress, GetJoinAddress, CreateJoinAddress, GetJoinAddress]
):
    def get_model(self):
        return self.model


addrDB = AsyncJoinAddressCRUD(JoinAddress)
