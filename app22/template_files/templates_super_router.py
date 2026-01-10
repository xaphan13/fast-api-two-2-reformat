from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column
from app22.db_core.db_async import async_db

from app22.template_files.templates_schema import Resp, Create, Get, OrderbyList
from app22.template_files.templates_async_crud import templatesDB
from app22.template_files.templates_model import TableName


templates_router = APIRouter(prefix="/templates_router", tags=["NEW templates_router"])


# ================================================================================
# ********* adding Order to the database *****************************************
@templates_router.post("/add_person", response_model=Resp)
async def add_person(body: Create, db: AsyncSession = Depends(async_db.get_db)):
    person: TableName = await templatesDB.add_record(body, db)
    return person


# ================================================================================
# ********* get one Order to the database ****************************************
@templates_router.get("/get_person", response_model=Resp)
async def get_person(params: Get = Depends(), db: AsyncSession = Depends(async_db.get_db)):
    person: TableName = await templatesDB.get_record_one(params, db)
    return person


# ================================================================================
# **************** get all Orders to the database ********************************
@templates_router.post("/get_all_person", response_model=list[Resp])
async def get_all_person(params: OrderbyList, db: AsyncSession = Depends(async_db.get_db)):
    order_by: list[Column[TableName]] = templatesDB.get_order_attr(params.order_by_list)
    result_all: list[TableName] = await templatesDB.get_all_records(order_by, db)
    return result_all
