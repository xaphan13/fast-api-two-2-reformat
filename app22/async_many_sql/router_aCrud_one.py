from app22.db_crud_base.async_crud_order import order_async, product_async
from app22.config_log import ConfigLogger

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column

from app22.async_many_sql.schema_many_sql import (
    OrderCreateBody,
    OrderGetAllOrderbyQuery,
    OrderResp,
    OrderGetQuery,
    OrderGetOrderbyList,
    OrderUpdateBody,
    ProductGetQuery,
    ProductResp,
)
from app22.db_core.db_async import async_db
from app22.db_core.model.model_new_many_db import Order, Product

logFC = ConfigLogger.get_logger("FileStdout")


new_many_aCrud_one = APIRouter(prefix="/new_many_aCrud_one", tags=["NEW new_many_aCrud_one"])


# ================================================================================
# ********* adding Order to the database *****************************************
@new_many_aCrud_one.post("/add_order", response_model=OrderResp)
async def add_order(body: OrderCreateBody, db: AsyncSession = Depends(async_db.get_db)):
    new_order: Order = await order_async.add_record(body, db)
    logFC.info(f"POST/add_order : new_order = {type(new_order)}")
    return new_order


# ================================================================================
# ********* get one Order to the database ****************************************
@new_many_aCrud_one.get("/get_order_one", response_model=OrderResp)
async def get_order_one(params: OrderGetQuery = Depends(), db: AsyncSession = Depends(async_db.get_db)):
    order: Order = await order_async.get_record_one(params, db)
    logFC.info(f"GET/filter_by : new_order = {type(order)}")
    if order is not None:
        return order
    raise HTTPException(status_code=422, detail=f"get_order with {params} not found")


# ================================================================================
# ********* get list Orders to the database **************************************
@new_many_aCrud_one.get("/get_order_list", response_model=list[OrderResp])
async def get_order_list(params: OrderGetQuery = Depends(), db: AsyncSession = Depends(async_db.get_db)):
    orders: list[Order] = await order_async.get_records_list(params, db)
    logFC.info(f"GET/order_where : stmt = {type(orders)}")
    return orders


# ================================================================================
# **************** get all Orders to the database ********************************
@new_many_aCrud_one.get("/get_all_orders", response_model=list[OrderResp])
async def get_all_orders(params: OrderGetAllOrderbyQuery, db: AsyncSession = Depends(async_db.get_db)):
    order_by_list_o: list[Column[Order]] = [Order.id, Order.created_at]
    if params == "time":
        order_by_list_o: list[Column[Order]] = [Order.created_at, Order.id]
    elif params == "promocode":
        order_by_list_o: list[Column[Order]] = [Order.promocode, Order.created_at]
    result_all: list[Order] = await order_async.get_all_records(order_by_list_o, db)
    return result_all


# ================================================================================
# **************** get all Orders to the database ********************************
@new_many_aCrud_one.post("/get_all_orders_new", response_model=list[OrderResp])
async def get_all_orders_new(params: OrderGetOrderbyList, db: AsyncSession = Depends(async_db.get_db)):
    order_by: list[Column[Order]] = order_async.get_order_attr(params.order_by_list)
    result_all: list[Order] = await order_async.get_all_records(order_by, db)
    return result_all


# ================================================================================
# updating Order to the database *****************************************
@new_many_aCrud_one.put("/update_order_one", response_model=OrderResp)
async def update_order_one(
    body: OrderUpdateBody, params: OrderGetQuery = Depends(), db: AsyncSession = Depends(async_db.get_db)
):
    order: Order = await order_async.get_record_one(params, db)
    logFC.info(f"UPDATE/update_order_one : search_order = {order}")

    order_up: Order = await order_async.update_record_one(order, body, db)
    if order_up is not None:
        return order_up
    raise HTTPException(status_code=422, detail=f"update_order_one with {params} not found")


# ================================================================================
# updating Order to the database *****************************************
@new_many_aCrud_one.put("/update_order_many", response_model=dict)
async def update_order_many(
    body: OrderUpdateBody, params: OrderGetQuery = Depends(), db: AsyncSession = Depends(async_db.get_db)
):
    qty_update = await order_async.update_record_many(params, body, db)
    logFC.info(f"UPDATE/update_order_many : {qty_update}")
    return {"qtyUPDATE": qty_update}


# deleting Order to the database *****************************************
@new_many_aCrud_one.delete("/delete_order_many", response_model=dict)
async def delete_order_many(params: OrderGetQuery = Depends(), db: AsyncSession = Depends(async_db.get_db)):
    qty_delete = await order_async.delete_record_many(params, db)
    logFC.info(f"DELETE/delete_order_many : {qty_delete}")
    return {"qtyDELETE": qty_delete}


# deleting Order to the database *****************************************
@new_many_aCrud_one.delete("/delete_order_one", response_model=OrderResp)
async def delete_order_one(params: OrderGetQuery = Depends(), db: AsyncSession = Depends(async_db.get_db)):
    order: Order = await order_async.get_record_one(params, db)
    logFC.info(f"DELETE/delete_order_one : search_order = {order}")

    order_del: Order = await order_async.delete_record_one(order, db)
    if order_del is not None:
        return order_del
    raise HTTPException(status_code=422, detail=f"delete_order_one with {params} not found")


@new_many_aCrud_one.delete("/delete_product_one", response_model=ProductResp)
async def delete_product_one(params: ProductGetQuery = Depends(), db: AsyncSession = Depends(async_db.get_db)):
    product: Product = await product_async.get_record_one(params, db)
    logFC.info(f"DELETE/delete_product_one : search_order = {product}")

    product_del: Product = await product_async.delete_record_one(product, db)
    if product_del is not None:
        return product_del
    raise HTTPException(status_code=422, detail=f"delete_product_one with {params} not found")
