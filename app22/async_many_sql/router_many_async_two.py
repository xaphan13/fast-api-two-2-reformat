from sqlalchemy import CursorResult, Delete, Update

from app22.config_log import ConfigLogger

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.sql import select, Select, update, delete
from sqlalchemy.engine import Result

from app22.async_many_sql.schema_many_sql import OrderResp, OrderGetQuery, OrderUpdateBody
from app22.db_core.db_async import async_db
from app22.db_core.model.model_new_many_db import Order


logFC = ConfigLogger.get_logger("FileStdout")


new_many_async_two = APIRouter(prefix="/new_many_async_two", tags=["NEW new_many_async_two"])


# ================================================================================
# +++++++++++++++++++++++++ deleting record +++++++++++++++++++++++++
# ================================================================================
# deleting Order to the database *****************************************
@new_many_async_two.delete("/delete_order", response_model=OrderResp)
async def delete_order(params: OrderGetQuery = Depends(), db: AsyncSession = Depends(async_db.get_db)):
    filter_delete = {key: value for key, value in params.model_dump(exclude_none=True).items()}
    stmt: Select[tuple[Order]] = select(Order).filter_by(**filter_delete)
    result: Result[tuple[Order]] = await db.execute(stmt)
    order: Order = result.scalar()

    logFC.info(f"DELETE/delete_order : search_order = {order}")
    if order is not None:
        await db.delete(order)
        await db.commit()
        return order
    raise HTTPException(status_code=422, detail=f"delete.filter_by with {filter_delete} not found")


# deleting Order to the database *****************************************
@new_many_async_two.delete("/delete_list_order", response_model=dict)
async def delete_list_order(params: OrderGetQuery = Depends(), db: AsyncSession = Depends(async_db.get_db)):
    # filter_filter_by = {key: value for key, value in params.model_dump(exclude_none=True).items()}
    # stmt: Delete[Any] = delete(Order).filter_by(**filter_filter_by)

    filter_where = [getattr(Order, key) == value for key, value in params.model_dump(exclude_none=True).items()]
    stmt: Delete[Order] = delete(Order).where(*filter_where)

    result: CursorResult[Order] = await db.execute(stmt)
    await db.commit()

    qty_delete = result.rowcount
    logFC.info(f"DELETE/delete_list_order : {qty_delete}- {type(qty_delete)} - {type(result)}")
    return {"DELETE": qty_delete}


# ================================================================================
# ================================================================================


# ================================================================================
# +++++++++++++++++++++++++ update record - condition  +++++++++++++++++++++++++
# ================================================================================
# updating Order to the database *****************************************
@new_many_async_two.put("/update_order", response_model=OrderResp)
async def update_order(
    body: OrderUpdateBody, params: OrderGetQuery = Depends(), db: AsyncSession = Depends(async_db.get_db)
):
    filter_update = {key: value for key, value in params.model_dump(exclude_none=True).items()}
    stmt: Select[tuple[Order]] = select(Order).filter_by(**filter_update)
    result: Result[tuple[Order]] = await db.execute(stmt)
    order: Order = result.scalar()

    logFC.info(f"UPDATE/update_order : search_order = {order}")
    if order is not None:
        for key, value in body.model_dump(exclude_unset=True).items():
            setattr(order, key, value)
        await db.commit()
        return order
    raise HTTPException(status_code=422, detail=f"update.filter_by with {filter_update} not found")


# updating Order to the database *****************************************
@new_many_async_two.put("/update_list_order", response_model=dict)
async def update_list_order(
    body: OrderUpdateBody, params: OrderGetQuery = Depends(), db: AsyncSession = Depends(async_db.get_db)
):
    filter_where = [getattr(Order, key) == value for key, value in params.model_dump(exclude_none=True).items()]

    update_values = body.model_dump(exclude_unset=True)

    stmt: Update[Order] = update(Order).where(*filter_where).values(**update_values)

    result: CursorResult[Order] = await db.execute(stmt)
    await db.commit()

    rowcount = result.rowcount
    logFC.info(f"UPDATE/update_list_order : {rowcount}- {type(stmt)} - {type(result)}")
    return {"UPDATE": rowcount}


# ================================================================================
# ================================================================================
