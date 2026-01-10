import os
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select
from sqlalchemy.orm import joinedload, aliased
from sqlalchemy import Row, func, desc, Result, Subquery, CTE
from typing import Tuple, Sequence, Any
from fastapi.responses import FileResponse

from app22.core.config import FILES_DIR
from app22.db_core.db_async import async_db
from app22.db_crud_base.async_reader import readerDB
from app22.db_core.db_models.model_reader_book import ListBook
from app22.async_reader_project.schema_relationship import *


from app22.config_log import ConfigLogger

logFC = ConfigLogger.get_logger("FileStdout")


reader_aCrud_two = APIRouter(prefix="/reader_aCrud_two", tags=["NEW reader_aCrud_two"])
# app.include_router(reader_aCrud_two)


# ================================================================================
# **************** get Reader with ListBook from the database ********************
@reader_aCrud_two.get(
    "/get_subquery_join",
    response_model=List[
        Tuple[SchemaReader, SchemaListBook | None, SchemaBook | None]
        | Tuple[SchemaReader, SchemaBook]
        | Tuple[SchemaReader, SchemaListBook]
    ],
)
async def get_subquery_join(params: SchemaReader = Depends(), db: AsyncSession = Depends(async_db.get_db)):
    where_attr: list = readerDB.get_filter_attr(params)

    query = select(Reader, ListBook, Book)
    query = query.where(*where_attr)
    query = query.distinct(Reader.id, Book.id)
    query = query.join(Reader.book_lists)
    query = query.join(ListBook.books)
    query = query.order_by(Reader.id, Book.id)
    subquery = query.subquery(name="subq")

    readerA = aliased(Reader, subquery, name="reader")
    listA = aliased(ListBook, subquery, name="list")
    bookA = aliased(Book, subquery, name="book")

    queryM = select(readerA, listA, bookA).select_from(subquery)
    queryM = queryM.order_by(listA.list_name)

    result = await db.execute(queryM)

    records: Sequence[Row[tuple[Reader, ListBook, Book]]] = result.all()
    for rec in records:
        logFC.info(f"{rec.reader} - {rec.list} - {rec.book}")  # logFC.info(f"{rec}")
    return records


# ================================================================================
# **************** get Reader with ListBook from the database ********************
@reader_aCrud_two.get(
    "/get_join_distinct",
    response_model=List[
        Tuple[SchemaReader, SchemaListBook | None, SchemaBook | None]
        | Tuple[SchemaReader, SchemaBook]
        | Tuple[SchemaReader, SchemaListBook]
    ],
)
async def get_join_distinct(params: SchemaReader = Depends(), db: AsyncSession = Depends(async_db.get_db)):
    where_attr: list = readerDB.get_filter_attr(params)

    query = select(Reader, ListBook, Book)
    query = query.where(*where_attr)
    # query = query.distinct(Reader.id, ListBook.id)
    query = query.distinct(Reader.id, Book.id)
    query = query.join(Reader.book_lists)  # query.outerjoin(Reader.book_lists)
    query = query.join(ListBook.books)  # query.outerjoin(ListBook.books)
    query = query.order_by(Reader.id, Book.id)

    result = await db.execute(query)

    records: Sequence[Row[tuple[Reader, ListBook, Book]]] = result.all()
    for rec in records:
        logFC.info(f"{rec}")
    return records


# ================================================================================
# ********* get one Order to the database ****************************************
@reader_aCrud_two.get("/get_unique_joinedload", response_model=List[SchemaReader])
async def get_unique_joinedload(params: SchemaReader = Depends(), db: AsyncSession = Depends(async_db.get_db)):
    where_attr: list = readerDB.get_filter_attr(params)
    query = select(Reader).where(where_attr)
    query = query.options(joinedload(ListBook.books))
    result = await db.execute(query)
    records: list = result.unique().scalars().all()
    for rec in records:
        logFC.info(f"{rec}")
    return records


# ================================================================================
# **************** get Reader with ListBook from the database ********************
@reader_aCrud_two.get("/get_having_cte", response_model=List[Tuple[SchemaReader, SchemaBook | None, int]])
async def get_having_cte(params: SchemaListBook = Depends(), db: AsyncSession = Depends(async_db.get_db)):
    where_attr: list = readerDB.get_filter_attr(params)  # outerjoin    join

    query = select(ListBook.reader_id, Book.title, func.count(Book.id).label("count"))
    query = query.where(*where_attr)
    query = query.outerjoin(ListBook.books)
    query = query.group_by(ListBook.reader_id, Book.title)
    query = query.having(func.count(Book.id) > -1)
    subquery = query.cte(name="subq")

    query = select(Reader, Book, subquery.c.count)
    query = query.join(subquery, Reader.id == subquery.c.reader_id)
    query = query.outerjoin(Book, Book.title == subquery.c.title)
    query = query.order_by(Reader.nickname, desc("count"))
    # query = query.order_by(desc("count"))

    result: Result[tuple[Reader, Book, Any]] = await db.execute(query)
    records: list = result.all()
    for rec in records:
        logFC.info(f"{rec}")
    return records


# ================================================================================
# **************** get Reader with ListBook from the database ********************
@reader_aCrud_two.get(
    "/get_subquery_count_book",
    response_model=List[
        QtyBookReader
        | Tuple[int, SchemaBook, SchemaReader]
        | Tuple[SchemaReader, SchemaBook, int]
        | Tuple[str | None, int | None]
    ],
)
async def get_subquery_count_book(params: SchemaListBook = Depends(), db: AsyncSession = Depends(async_db.get_db)):
    where_attr: list = readerDB.get_filter_attr(params)  # outerjoin    join

    query = select(Book, ListBook.reader_id)
    query = query.join(Book.lists)
    query = query.distinct(Book.id, ListBook.reader_id)
    query = query.order_by(Book.id, ListBook.reader_id)
    subquery: Subquery = query.subquery(name="subQ")

    listAliased = aliased(ListBook, subquery, name="listA")
    bookAliased = aliased(Book, subquery, name="bookA")

    query = select(bookAliased.id, func.count(bookAliased.id).label("countB"))
    query = query.group_by(bookAliased.id)
    query = query.having(func.count(bookAliased.id) > 1)
    ctequery: CTE = query.cte(name="cteQ")

    query = select(ctequery.c.countB, bookAliased, Reader)
    query = query.join(subquery, listAliased.reader_id == Reader.id)
    query = query.join(ctequery, ctequery.c.id == bookAliased.id)
    query = query.order_by(desc(ctequery.c.countB), bookAliased.id)

    result: Result = await db.execute(query)
    records = result.all()
    for rec in records:
        logFC.info(f"{rec}")

    qty_books: dict[int, QtyBookReader] = {}
    for qty, book, reader in records:  # type: int, Book, Reader
        hhh = qty_books.setdefault(book.id, QtyBookReader(qty_all=qty).set_book(book))
        hhh.append_reader(reader=reader)
    logFC.info(f"{list(qty_books.values())}")
    return qty_books.values()


# ================================================================================
# ************* UploadFile upload_file + download_file FileResponse ***************
@reader_aCrud_two.post("/upload_file", response_model=dict)
async def upload_file(file: UploadFile = File(...), file_info: UploadFileReq = Depends()):
    dirF: str = FILES_DIR if file_info.dir_name is None else f"app22/{file_info.dir_name}"
    fileN: str = file.filename if file_info.file_name is None else file_info.file_name

    if os.path.exists(f"{dirF}/{fileN}") is True:
        raise HTTPException(status_code=404, detail="File already exists")

    with open(f"{dirF}/{fileN}", "wb") as buffer:
        buffer.write(await file.read())

    ret: dict[Any, Any] = dict(file.__dict__)
    return {"name": fileN, "size": ret["size"]}


@reader_aCrud_two.get("/download_file", response_class=FileResponse)
async def download_file(file: DownloadFileReq = Depends()):
    dirF: str = FILES_DIR if file.dir_name is None else f"app22/{file.dir_name}"

    if os.path.exists(f"{dirF}/{file.file_name}") is False:
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path=f"{dirF}/{file.file_name}", filename=file.file_name, media_type="application/octet-stream")
