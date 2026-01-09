from fastapi import APIRouter, Depends, HTTPException
from typing import Type, Optional

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session, selectinload, joinedload

from app11.example_many_db.except_many_db import MyApiRouterMany
from app11.logger_core.config_logger import ConfigLogger
from app11.db_core.db_conf import SessionDB

from app11.example_many_db.model_many_db import Order, Product
from app11.example_many_db.crud_many import order_db, product_db

from app11.example_many_db.schema_many_db import (
    OrderResp,
    ProductResp,
    OrderGetQuery,
    OrderUpdateBody,
    OrderCreateBody,
    ProductGetQuery,
    ProductUpdateBody,
    ProductCreateBody,
    ProductRespWithOrders,
    ProductRespWithsAssoc,
    ProductRespWithOrdersAssoc,
    TypeResponse,
)


ex_many_route = APIRouter(route_class=MyApiRouterMany, prefix="/ex_many", tags=["ex_many"])
logFC = ConfigLogger.getLogger("FileStdout", "ex_assoc")


# ***************************************************************************************
# Orders requesting to dataBase =========================================================
# ---------------------------------------------------------------------------------------
# adding Order to the database **********************************************************
@ex_many_route.post("/add_order", response_model=OrderResp, status_code=200)
def add_order(body: OrderCreateBody, db: Session = Depends(SessionDB.get_db)):
    new_order: Order = order_db.add_record(body, db)
    return new_order


# requesting Order from the database ****************************************************
@ex_many_route.get("/get_order_first", response_model=OrderResp, status_code=200)
def get_order_first(query: OrderGetQuery = Depends(), db: Session = Depends(SessionDB.get_db)):
    order: Order = order_db.get_record_schema_raise(query, db)
    return order


# updating Order from the database ******************************************************
@ex_many_route.put("/update_order", response_model=OrderResp)
def update_order(body: OrderUpdateBody, db: Session = Depends(SessionDB.get_db), query: OrderGetQuery = Depends()):
    order: Order = order_db.update_record(query, body, db)
    return order


# deleting Order from the database ******************************************************
@ex_many_route.delete("/delete_order", response_model=OrderResp)
def delete_order(query: OrderGetQuery = Depends(), db: Session = Depends(SessionDB.get_db)):
    order: Order = order_db.delete_record(query, db)
    return order


# deleting All Orders from the database ******************************************************
@ex_many_route.delete("/delete_all_order")
def delete_all_order(db: Session = Depends(SessionDB.get_db)) -> dict[str, int]:
    res = order_db.delete_all(db)
    return res


# requesting list all Orders from the database ******************************************
@ex_many_route.get("/get_order_all", response_model=list[OrderResp], status_code=200)
def get_order_all(db: Session = Depends(SessionDB.get_db)):
    orders: list[Type[Order]] = order_db.get_record_all(db)
    return orders


# requesting list of Order from the database ********************************************
@ex_many_route.get("/get_order_part", response_model=list[OrderResp], status_code=200)
def get_order_part(begin: int, length: int, db: Session = Depends(SessionDB.get_db)):
    orders: list[Type[Order]] = order_db.get_record_part(begin=begin, length=length, db=db)
    return orders


# ***************************************************************************************
# Products requesting to dataBase =======================================================
# ---------------------------------------------------------------------------------------
# adding Product to the database ********************************************************
@ex_many_route.post("/add_product", response_model=ProductResp, status_code=200)
def add_product(body: ProductCreateBody, db: Session = Depends(SessionDB.get_db)):
    new_product: Product = product_db.add_record(body, db)
    return new_product


# requesting Product from the database **************************************************
@ex_many_route.get(
    "/get_product_first",
    response_model=ProductRespWithOrdersAssoc | ProductRespWithsAssoc | ProductRespWithOrders | ProductResp,
)
def get_product_first(
    type_response: TypeResponse, query: ProductGetQuery = Depends(), db: Session = Depends(SessionDB.get_db)
):
    # product: Product = product_db.get_record_schema_raise(query, db)
    query_dict = {key: value for key, value in query.dict().items() if value is not None}
    product: Optional[Product] = (
        db.query(Product)
        .options(joinedload(Product.orders), selectinload(Product.orders_details))
        .filter_by(**query_dict)
        .first()
    )
    if product is None:
        raise HTTPException(status_code=422, detail=f"Product.filter_by with {query_dict} not found")

    obj_data = jsonable_encoder(product)
    if type_response == 1:
        schema: ProductResp = ProductResp(**obj_data)
    elif type_response == 2:
        schema: ProductRespWithOrders = ProductRespWithOrders(**obj_data)
    elif type_response == 3:
        schema: ProductRespWithsAssoc = ProductRespWithsAssoc(**obj_data)
    elif type_response == 4:
        schema: ProductRespWithOrdersAssoc = ProductRespWithOrdersAssoc(**obj_data)
    else:
        schema: ProductResp = ProductResp()
    return schema


# requesting list of Product from the database ******************************************
@ex_many_route.get("/get_product_all", response_model=list[ProductRespWithOrdersAssoc], status_code=200)
def get_product_all(db: Session = Depends(SessionDB.get_db)):
    products: list[Type[Product]] = product_db.get_record_all(db)
    return products


# updating Product from the database ****************************************************
@ex_many_route.put("/update_product", response_model=ProductResp)
def update_product(
    body: ProductUpdateBody, db: Session = Depends(SessionDB.get_db), query: ProductGetQuery = Depends()
):
    product: Product = product_db.update_record(query, body, db)
    return product


# deleting Product from the database ****************************************************
@ex_many_route.delete("/delete_product", response_model=ProductResp)
def delete_product(query: ProductGetQuery = Depends(), db: Session = Depends(SessionDB.get_db)):
    product: Product = product_db.delete_record(query, db)
    return product


# deleting All Products from the database ******************************************************
@ex_many_route.delete("/delete_all_product")
def delete_all_product(db: Session = Depends(SessionDB.get_db)) -> dict[str, int]:
    res = product_db.delete_all(db)
    return res


# requesting list all Products from the database ****************************************
@ex_many_route.get("/get_product_part", response_model=list[ProductResp], status_code=200)
def get_product_part(begin: int, length: int, db: Session = Depends(SessionDB.get_db)):
    products: list[Type[Product]] = product_db.get_record_part(begin=begin, length=length, db=db)
    return products
