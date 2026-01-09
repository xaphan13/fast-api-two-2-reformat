from app22.logger_core.config_logger import ConfigLogger
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app22.reader_project.schema_reader import CreateReader, SchemaReader
from app22.db_core.db_async import async_db
from app22.db_crud_base.async_reader import readerDB
from app22.db_core.model.model_reader_book import Reader


logFC = ConfigLogger.getLogger("FileStdout", "reader_aCrud_one")


reader_aCrud_one = APIRouter(prefix="/reader_aCrud_one", tags=["NEW reader_aCrud_one"])
# app.include_router(reader_aCrud_one)


# ================================================================================
# ********* adding Order to the database *****************************************
@reader_aCrud_one.post("/add_", response_model=dict)
async def add_(body: CreateReader, db: AsyncSession = Depends(async_db.get_db)):
    reader: Reader = await readerDB.add_record(body, db)
    return {"add_": "add_"}


# ================================================================================
# ********* get one Order to the database ****************************************
@reader_aCrud_one.get("/get_", response_model=dict)
async def get_(params: SchemaReader = Depends(), db: AsyncSession = Depends(async_db.get_db)):
    if params is not None:
        return {"get_": "get_"}
    raise HTTPException(status_code=422, detail=f"get_ with {params} not found")


# ================================================================================
# updating Order to the database *****************************************
@reader_aCrud_one.put("/update_", response_model=dict)
async def update_(body: SchemaReader, params: SchemaReader = Depends(), db: AsyncSession = Depends(async_db.get_db)):
    if body is not None:
        logFC.info(f"POST/update_ : new_ = {type(body)}")
        return {"update_": "update_"}
    raise HTTPException(status_code=422, detail=f"update_ with {params} not found")


# deleting Order to the database *****************************************
@reader_aCrud_one.delete("/delete_", response_model=dict)
async def delete_(params: SchemaReader = Depends(), db: AsyncSession = Depends(async_db.get_db)):
    return {"delete_": "delete_"}
