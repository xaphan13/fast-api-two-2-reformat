from app22.async_many_sql.schema_many_sql import (
    AssociationGetQuery,
    OrderCreateBody,
    OrderGetQuery,
    OrderUpdateBody,
    ProductCreateBody,
    ProductGetQuery,
    ProductUpdateBody,
)

from app22.async_many_sql.model_new_many_db import (
    Order,
    Product,
    OrderProductAssociation,
)

from app22.not_async_examples.not_async_crud_base import NewCRUDBase


class OrderCRUD(
    NewCRUDBase[
        Order,
        OrderCreateBody,
        OrderGetQuery,
        OrderUpdateBody,
        OrderGetQuery,
    ]
):
    def get_model(self):
        return self.model


class ProductCRUD(
    NewCRUDBase[
        Product,
        ProductCreateBody,
        ProductGetQuery,
        ProductUpdateBody,
        ProductGetQuery,
    ]
):
    def get_model(self):
        return self.model


class OrderProductAssociationCRUD(
    NewCRUDBase[
        OrderProductAssociation,
        AssociationGetQuery,
        AssociationGetQuery,
        AssociationGetQuery,
        AssociationGetQuery,
    ]
):
    def get_model(self):
        return self.model


order_crud = OrderCRUD(Order)
product_db = ProductCRUD(Product)
association_db = ProductCRUD(OrderProductAssociation)
