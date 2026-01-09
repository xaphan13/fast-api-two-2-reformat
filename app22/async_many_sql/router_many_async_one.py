from sqlalchemy.orm import joinedload

from app22.config_log import ConfigLogger

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import Column, Row
from sqlalchemy.sql import select, Select, insert, Insert
from sqlalchemy.engine import Result

from typing import Sequence

from app22.async_many_sql.schema_many_sql import (
    OrderCreateBody,
    OrderGetAllOrderbyQuery,
    OrderResp,
    ProductResp,
    OrderGetQuery,
)

from app22.db_core.db_async import async_db
from app22.db_core.model.model_new_many_db import Order, Product


logFC = ConfigLogger.get_logger("FileStdout")


new_many_async_one = APIRouter(prefix="/new_many_async_one", tags=["NEW new_many_async_one"])


# ================================================================================
# +++++++++++++++++++++++++ added record +++++++++++++++++++++++++
# ================================================================================
# adding Order to the database *****************************************
@new_many_async_one.post("/add_order", response_model=OrderResp)
async def add_order(body: OrderCreateBody, db: AsyncSession = Depends(async_db.get_db)):
    new_order: Order = Order(**body.model_dump())
    db.add(new_order)

    await db.commit()
    await db.refresh(new_order)

    logFC.info(f"POST/add_order : new_order = {type(new_order)}")
    return new_order


# adding Order to the database *****************************************
@new_many_async_one.post("/insert_order", response_model=OrderCreateBody)
async def insert_order(body: OrderCreateBody, db: AsyncSession = Depends(async_db.get_db)):
    stmt: Insert[Order] = insert(Order).values(**body.model_dump())

    await db.execute(stmt)
    await db.commit()

    logFC.info(f"POST/insert_order : stmt = {type(stmt)}")
    return body


# ================================================================================
# ================================================================================


# ================================================================================
# +++++++++++++++++++++++++ get record - condition  +++++++++++++++++++++++++
# ================================================================================
# get Order to the database *****************************************
@new_many_async_one.get("/get_order_filter_by", response_model=OrderResp)
async def get_order_filter_by(params: OrderGetQuery = Depends(), db: AsyncSession = Depends(async_db.get_db)):
    # stmt: Select[tuple[Order]] = select(Order).filter_by(id=22)
    filter_where = {key: value for key, value in params.model_dump().items() if value is not None}

    stmt: Select[tuple[Order]] = select(Order).filter_by(**filter_where)
    logFC.info(f"GET/filter_by : filter_where = \n{filter_where}")

    result: Result[tuple[Order]] = await db.execute(stmt)

    order: Order = result.scalar()

    logFC.info(f"GET/filter_by : new_order = {type(order)}")
    if order is not None:
        return order
    raise HTTPException(status_code=422, detail=f"select.filter_by with {filter_where} not found")


# get Order to the database *****************************************
@new_many_async_one.get("/get_order_where", response_model=OrderResp | list[OrderResp])
async def get_order_where(params: OrderGetQuery = Depends(), db: AsyncSession = Depends(async_db.get_db)):
    # stmt = select(Order).where(Order.id == 22)
    filter_where = [getattr(Order, key) == value for key, value in params.model_dump(exclude_none=True).items()]

    # filter_where = [getattr(Order, key) > value
    #                 for key, value in params.dict(exclude_none=True).items()]

    stmt = select(Order).where(*filter_where)
    logFC.info(f"GET/order_where : filter_where = \n{filter_where}")

    result = await db.execute(stmt)

    # orders: Order = result.scalar()
    # orders: Order = result.scalars().first()
    orders: Sequence[Order] = result.scalars().all()

    logFC.info(f"GET/order_where : stmt = {type(orders)}")
    if orders is None:
        raise HTTPException(status_code=422, detail=f"select.where with {filter_where} not found")
    return orders


# ================================================================================
# ================================================================================


# ================================================================================
# +++++++++++++++++++++++++ get all - order_by +++++++++++++++++++++++++
# ================================================================================
# get all Order to the database **********************************************************
@new_many_async_one.get("/get_all_orders", response_model=list[OrderResp])
async def get_all_orders(params: OrderGetAllOrderbyQuery, db: AsyncSession = Depends(async_db.get_db)):
    if params == "time":
        order_by_list_o: list[Column[Order]] = [Order.created_at, Order.id]
    elif params == "promocode":
        order_by_list_o: list[Column[Order]] = [Order.promocode, Order.created_at]
    else:
        order_by_list_o: list[Column[Order]] = [Order.id, Order.created_at]
    # =====================================================================

    stmt: Select[tuple[Order]] = select(Order).order_by(*order_by_list_o)

    await_result_execute: Result[tuple[Order]] = await db.execute(stmt)
    result_scalars_all: Sequence[Order] = await_result_execute.scalars().all()

    return result_scalars_all


# ================================================================================
# ================================================================================


# ================================================================================
# +++++++++++++++++++++++++ test +++++++++++++++++++++++++
# ================================================================================
# test Order to the database **********************************************************
@new_many_async_one.get("/get_all_test", response_model=list[ProductResp | OrderResp])
async def get_all_orders(variant: int = 1, db: AsyncSession = Depends(async_db.get_db)):
    stmt: Select[tuple[Order]] = (
        select(Order)
        .order_by(Order.id)
        # .options(selectinload(Order.products))
        .options(joinedload(Order.products))
    )
    await_result_execute: Result[tuple[Order]] = await db.execute(stmt)

    if variant == 1:
        result_scalars_all: Sequence[Order] = await_result_execute.unique().scalars().all()
        order0: Order = result_scalars_all[0]
        order1: Order = result_scalars_all[1]
    else:
        result_all: Sequence[Row[tuple[Order]]] = await_result_execute.unique().all()
        row0: Row[tuple[Order]] = result_all[0]
        order0: Order = row0[0]
        row1: Row[tuple[Order]] = result_all[1]
        order1: Order = row1[0]

    prods0: list[Product] = order0.products
    logFC.info(f"POST/all : 'order0' = {order0}")
    [logFC.info(f"POST/all : prods0 = {prod}") for prod in prods0]

    prods1: list[Product] = order1.products
    logFC.info(f"POST/all : 'order1' = {order1}")
    [logFC.info(f"POST/all : prods1 = {prod}") for prod in prods1]

    return [order0] + prods0 + [order1] + prods1


# ================================================================================
# ================================================================================
