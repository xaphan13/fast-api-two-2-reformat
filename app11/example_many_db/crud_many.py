from app11.example_many_db.crud_base import CRUDBase
from app11.example_many_db.schema_many_db import (
    OrderCreateBody,
    OrderGetQuery,
    OrderUpdateBody,
    ProductCreateBody,
    ProductGetQuery,
    ProductUpdateBody,
    AssociationGetQuery,
)

from app11.example_many_db.model_many_db import Order, Product, OrderProductAssociation


class OrderCRUD(CRUDBase[Order, OrderCreateBody, OrderGetQuery, OrderUpdateBody, OrderGetQuery]):
    def get_model(self):
        return self.model


class ProductCRUD(CRUDBase[Product, ProductCreateBody, ProductGetQuery, ProductUpdateBody, ProductGetQuery]):
    def get_model(self):
        return self.model


class OrderProductAssociationCRUD(
    CRUDBase[
        OrderProductAssociation, AssociationGetQuery, AssociationGetQuery, AssociationGetQuery, AssociationGetQuery
    ]
):
    def get_model(self):
        return self.model


order_db = OrderCRUD(Order)
product_db = ProductCRUD(Product)
association_db = ProductCRUD(OrderProductAssociation)
