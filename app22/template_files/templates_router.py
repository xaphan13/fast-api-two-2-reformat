from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app22.db_core.db_async import async_db

from app22.template_files.templates_schema import Resp, Create, Get


templates_router = APIRouter(prefix="/templates_router", tags=["NEW templates_router"])


# ================================================================================
# ********* adding Order to the database *****************************************
@templates_router.post("/add_", response_model=Resp)
async def add_(body: Create, db: AsyncSession = Depends(async_db.get_db)):
    return


# ================================================================================
# ********* get one Order to the database ****************************************
@templates_router.get("/get_", response_model=Resp)
async def get_(params: Get = Depends(), db: AsyncSession = Depends(async_db.get_db)):
    raise HTTPException(status_code=422, detail=f" with {params} not found")


# ================================================================================
# updating Order to the database *****************************************
@templates_router.put("/update_", response_model=Resp)
async def update_(body: Create, params: Get = Depends(), db: AsyncSession = Depends(async_db.get_db)):
    raise HTTPException(status_code=422, detail=f" with {params} not found")


# deleting Order to the database *****************************************
@templates_router.delete("/delete_", response_model=Resp)
async def delete_(params: Get = Depends(), db: AsyncSession = Depends(async_db.get_db)):
    raise HTTPException(status_code=422, detail=f" with {params} not found")
