from app22.logger_core.config_logger import ConfigLogger
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from sqlalchemy import Column

from app22.async_many_sql.schema_many_sql import OrderCreateBody, OrderResp, OrderGetAllOrderbyQuery

from app22.db_core.db_conf import SessionDB
from app22.db_crud_base.new_crud_many import order_crud
from app22.db_core.model.model_new_many_db import Order


logFC = ConfigLogger.getLogger("FileStdout", "new_many_crud")

new_many_crud = APIRouter(prefix="/new_many_crud", tags=["NEW new_many_crud"])


# adding Order to the database **********************************************************
@new_many_crud.post("/add_order_crud", response_model=OrderResp)
async def add_order_crud(body: OrderCreateBody, db: Session = Depends(SessionDB.get_db)):
    new_order: Order = order_crud.add_record(body, db)
    return new_order


# adding Order to the database **********************************************************
@new_many_crud.get("/get_all_orders_crud", response_model=list[OrderResp])
async def get_all_orders_crud(params: OrderGetAllOrderbyQuery, db: Session = Depends(SessionDB.get_db)):
    if params == "time":
        order_by_list_o: list[Column[Order]] = [Order.created_at, Order.id]
    elif params == "promocode":
        order_by_list_o: list[Column[Order]] = [Order.promocode, Order.created_at]
    else:
        order_by_list_o: list[Column[Order]] = [Order.id, Order.created_at]
    # =====================================================================

    orders: list[Order] = order_crud.get_record_all(db, order_by_list_o)
    return orders
