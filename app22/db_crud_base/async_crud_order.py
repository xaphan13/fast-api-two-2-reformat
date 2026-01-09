from app22.async_many_sql.schema_many_sql import (
    OrderCreateBody,
    OrderGetQuery,
    OrderUpdateBody,
    ProductCreateBody,
    ProductUpdateBody,
    ProductGetQuery,
)
from app22.db_crud_base.async_crud_base import AsyncBaseCRUD, ReaderType
from app22.db_core.model.model_new_many_db import Order, Product

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from sqlalchemy.orm import selectinload


class AsyncOrderCRUD(AsyncBaseCRUD[Order, OrderCreateBody, OrderGetQuery, OrderUpdateBody, OrderGetQuery]):
    def get_model(self):
        return self.model

    async def delete_record_many(self, search: ReaderType, db: AsyncSession):
        filter_attr = self._get_filter_attr(search)
        query = delete(self.model).where(*filter_attr)
        # ___________________ await  async  delete  all ____________________
        result = await db.execute(query)
        await db.commit()
        qty_delete = result.rowcount
        return qty_delete


order_async = AsyncOrderCRUD(Order)


class AsyncProductCRUD(AsyncBaseCRUD[Product, ProductCreateBody, ProductGetQuery, ProductUpdateBody, ProductGetQuery]):
    def get_model(self):
        return self.model


product_async = AsyncProductCRUD(Product)
