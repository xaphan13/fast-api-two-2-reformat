from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Column

from sqlalchemy.ext.asyncio import AsyncSession
from app22.db_core.db_async import async_db

from app22.async_many_sql.schema_many_sql import (
    OrderCreateBody,
    OrderGetAllOrderbyQuery,
    OrderResp,
    OrderGetQuery,
    OrderGetOrderbyList,
)


from app22.async_many_sql.model_new_many_db import Order

from app22.async_many_sql.async_crud_order import order_async

from app22.config_log import ConfigLogger

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
