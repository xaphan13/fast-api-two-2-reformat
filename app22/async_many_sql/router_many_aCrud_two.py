from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from app22.db_core.db_async import async_db

from app22.async_many_sql.schema_many_sql import (
    OrderResp,
    OrderGetQuery,
    OrderUpdateBody,
    ProductGetQuery,
    ProductResp,
)


from app22.async_many_sql.model_new_many_db import Order, Product

from app22.async_many_sql.async_crud_order import order_async, product_async

from app22.config_log import ConfigLogger

logFC = ConfigLogger.get_logger("FileStdout")


new_many_aCrud_two = APIRouter(prefix="/new_many_aCrud_two", tags=["NEW new_many_aCrud_two"])


# ================================================================================
# updating Order to the database *****************************************
@new_many_aCrud_two.put("/update_order_one", response_model=OrderResp)
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
@new_many_aCrud_two.put("/update_order_many", response_model=dict)
async def update_order_many(
    body: OrderUpdateBody, params: OrderGetQuery = Depends(), db: AsyncSession = Depends(async_db.get_db)
):
    qty_update = await order_async.update_record_many(params, body, db)
    logFC.info(f"UPDATE/update_order_many : {qty_update}")
    return {"qtyUPDATE": qty_update}


# ================================================================================
# deleting Order to the database *****************************************
@new_many_aCrud_two.delete("/delete_order_many", response_model=dict)
async def delete_order_many(params: OrderGetQuery = Depends(), db: AsyncSession = Depends(async_db.get_db)):
    qty_delete = await order_async.delete_record_many(params, db)
    logFC.info(f"DELETE/delete_order_many : {qty_delete}")
    return {"qtyDELETE": qty_delete}


# ================================================================================
# deleting Order to the database *****************************************
@new_many_aCrud_two.delete("/delete_order_one", response_model=OrderResp)
async def delete_order_one(params: OrderGetQuery = Depends(), db: AsyncSession = Depends(async_db.get_db)):
    order: Order = await order_async.get_record_one(params, db)
    logFC.info(f"DELETE/delete_order_one : search_order = {order}")

    order_del: Order = await order_async.delete_record_one(order, db)
    if order_del is not None:
        return order_del
    raise HTTPException(status_code=422, detail=f"delete_order_one with {params} not found")


# ================================================================================
# deleting Product to the database *****************************************
@new_many_aCrud_two.delete("/delete_product_one", response_model=ProductResp)
async def delete_product_one(params: ProductGetQuery = Depends(), db: AsyncSession = Depends(async_db.get_db)):
    product: Product = await product_async.get_record_one(params, db)
    logFC.info(f"DELETE/delete_product_one : search_order = {product}")

    product_del: Product = await product_async.delete_record_one(product, db)
    if product_del is not None:
        return product_del
    raise HTTPException(status_code=422, detail=f"delete_product_one with {params} not found")
