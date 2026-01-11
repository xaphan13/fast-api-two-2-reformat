from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, Row
from sqlalchemy.sql import select
from sqlalchemy.orm import selectinload
from typing import Tuple, Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from app22.db_core.db_async import async_db

from app22.async_reader_project.schema_reader import *
from app22.async_reader_project.schema_relationship import *

from app22.async_reader_project.model_reader_book import ListBook

from app22.db_core.async_crud_base import AddResult
from app22.async_reader_project.async_crud_reader import readerDB, listbookDB, bookDB, categoryDB

from app22.config_log import ConfigLogger


logFC = ConfigLogger.get_logger("FileStdout")


reader_aCrud_one = APIRouter(prefix="/reader_aCrud_one", tags=["NEW reader_aCrud_one"])


# ================================================================================
# ********************** adding Reader to the database ***************************
@reader_aCrud_one.post("/add_reader", response_model=SchemaReader)
async def add_reader(body: CreateReader, db: AsyncSession = Depends(async_db.get_db)):
    reader: AddResult = await readerDB.add_record_try(body, db)
    if not reader.result:
        raise HTTPException(status_code=422, detail=f"add error {reader.str_detail()}")
    return reader.model


# ================================================================================
# ******************** adding ListBook to the database ***************************
@reader_aCrud_one.post("/add_list_to_reader", response_model=SchemaListBook)
async def add_list_to_reader(
    body: CreateListBook, params: SchemaReader = Depends(), db: AsyncSession = Depends(async_db.get_db)
):
    reader: Reader = await readerDB.get_record_one(params, db)
    if reader is None:
        raise HTTPException(status_code=422, detail=f"reader with {params} not found")

    listbook: AddResult = await listbookDB.add_record_try(body.set_reader(reader.id), db)
    if not listbook.result:
        raise HTTPException(status_code=422, detail=f"add error {listbook.str_detail()}")
    return listbook.model


# ================================================================================
# ********************** adding Book to the database ***************************
@reader_aCrud_one.post("/add_book", response_model=SchemaBook)
async def add_book(body: CreateBook, db: AsyncSession = Depends(async_db.get_db)):
    book: AddResult = await bookDB.add_record_try(body, db)
    if not book.result:
        raise HTTPException(status_code=422, detail=f"add error {book.str_detail()}")
    return book.model


# ================================================================================
# ********************** adding Book to the database *****************************
@reader_aCrud_one.post("/create_add_book_to_list", response_model=SchemaBook)
async def create_add_book_to_list(
    body: CreateBook, params: SchemaAddBook = Depends(), db: AsyncSession = Depends(async_db.get_db)
):
    sch_reader = SchemaReader(id=params.reader_id, nickname=params.reader_nickname)

    # reader = await readerDB.get_reader_bookL_one(sch_reader, db)
    reader = await readerDB.get_record_rel_one(sch_reader, load=[Reader.book_lists], db=db)

    if reader is None:
        raise HTTPException(status_code=422, detail=f"reader with {params} not found")

    for listB in reader.book_lists:  # type: ListBook
        if params.list_id is None or listB.id == params.list_id:
            if listB.list_name == params.list_name:
                book: Book = await bookDB.add_book_to_list(body, db, listB)
                return book
    raise HTTPException(status_code=422, detail=f"book_list with {params} not found")


# ================================================================================
# ********************** adding Book to the database *****************************
@reader_aCrud_one.put("/add_exist_book_to_list", response_model=Tuple[ListBookReaderBooks, SchemaBookWithCategory])
async def add_new_book_to_list(
    body_book: SchemaBook,
    filterReader: ReaderAddBooks = Depends(),
    filterList: ListBookAddBooks = Depends(),
    db: AsyncSession = Depends(async_db.get_db),
):
    where_reader = readerDB.get_filter_attr(filterReader)  # nickname = reader_nickname
    where_list = listbookDB.get_filter_attr(filterList)  # list_name= list_name
    if not where_reader:
        raise HTTPException(status_code=422, detail=f"where_reader = {where_reader} : empty")

    query = (
        select(ListBook)
        .options(selectinload(ListBook.reader))
        .options(selectinload(ListBook.books))
        .join(Reader)
        .where(and_(*where_reader, *where_list))
    )

    result = await db.execute(query)
    listBooks: list[ListBook] = list(result.scalars().all())
    logFC.info(f"   listBooks = {len(listBooks)}\n{listBooks}")
    if not listBooks:
        raise HTTPException(status_code=422, detail=f"Not found ListBook : with {filterReader} {filterList}")
    elif len(listBooks) > 1:
        raise HTTPException(status_code=422, detail=f"More than one ListBook : with {filterReader} {filterList}")

    list_rel = [Book.categories, Book.lists]
    books: list[Book] = await bookDB.get_records_rel_list(body_book, load=list_rel, db=db)
    if not books:
        raise HTTPException(status_code=422, detail=f"Not found Book : with {body_book}")
    elif len(listBooks) > 1:
        raise HTTPException(status_code=422, detail=f"More than one Book : with {body_book}")

    listB: ListBook = listBooks[0]
    book: Book = books[0]

    listB.books.append(book)
    await db.commit()
    await db.refresh(listB)
    return listB, book


# ================================================================================
# **************** get Reader with ListBook from the database ********************
@reader_aCrud_one.get("/get_reader", response_model=ReaderLists)
async def get_reader(params: SchemaReader = Depends(), db: AsyncSession = Depends(async_db.get_db)):
    reader = await readerDB.get_record_rel_one(params, load=[Reader.book_lists], db=db)
    if reader is not None:
        return reader  # {"reader": db_json(reader)}
    raise HTTPException(status_code=422, detail=f"get_reader with {params} not found")


# ================================================================================
# **************** get Reader with ListBook from the database ********************
@reader_aCrud_one.get(
    "/get_book",
    response_model=List[SchemaBookWithCategoryLists | SchemaBookWithLists | SchemaBookWithCategory | SchemaBook],
)
async def get_book(
    params: SchemaBook = Depends(),
    relation: SchemaGetBookRel = Depends(),
    order: OrderbyBook = Depends(),
    db: AsyncSession = Depends(async_db.get_db),
):
    list_rel = []
    if relation.select == GetBookRelEnum.lists:
        list_rel = [Book.lists]
    elif relation.select == GetBookRelEnum.categories:
        list_rel = [Book.categories]
    elif relation.select == GetBookRelEnum.all:
        list_rel = [Book.categories, Book.lists]

    order_by = bookDB.get_order_attr([order.order_by.value])

    book = await bookDB.get_order_rel_list(params, load=list_rel, db=db, order_by=order_by)
    if book:
        return book
    raise HTTPException(status_code=422, detail=f"get_book with {params} not found")


# ================================================================================
# ******************* deleting Order to the database *****************************
@reader_aCrud_one.delete("/delete_all_or_id", response_model=list[int] | None)
async def delete_all_or_id(params: SchemaDeleteId = Depends(), db: AsyncSession = Depends(async_db.get_db)):
    qty_R, qty_L, qty_B, qty_C = 0, 0, 0, 0
    if params.type_del == DeleteEnum.reader:
        qty_R = await readerDB.delete_all_or_id(db, params.id)
    elif params.type_del == DeleteEnum.list:
        qty_L = await listbookDB.delete_all_or_id(db, params.id)
    elif params.type_del == DeleteEnum.book:
        qty_B = await bookDB.delete_all_or_id(db, params.id)
    elif params.type_del == DeleteEnum.category:
        qty_C = await categoryDB.delete_all_or_id(db, params.id)
    return [qty_R, qty_L, qty_B, qty_C]


# ================================================================================
# ================================================================================
# ++++++++++++++++++++++++++ examples examples examples ++++++++++++++++++++++++++
# ================================================================================
# ================================================================================
@reader_aCrud_one.put("/examples_book_list", response_model=List[Tuple[SchemaListBook, SchemaReader]])
async def examples_book_list(
    # filterReader: ReaderAddBooks = Depends(),
    # filterList: ListBookAddBooks = Depends(),
    db: AsyncSession = Depends(async_db.get_db),
):
    # where_reader = readerDB.get_filter_attr(filterReader)
    # where_list = listbookDB.get_filter_attr(filterList)
    # query = (select(ListBook)
    # .options(selectinload(ListBook.reader))
    # .join(Reader, ListBook.id < Reader.id)
    # .where(and_(*where_reader, *where_list))  # .where(*where_list)
    # )

    query = (
        select(ListBook, Reader)
        # .join(Reader, ListBook.id > Reader.user_id)
        .join(Reader, ListBook.reader_id == Reader.id)
        .where(and_(ListBook.list_name == "aaa", Reader.nickname == "Den"))
        # .where(and_(ListBook.list_name == "aaa", Reader.id == 34))
        # .where(and_(ListBook.list_name == "aaa", ListBook.reader_id == 34))
    )

    result = await db.execute(query)

    listBooks: Sequence[Row[tuple[ListBook, Reader]]] = result.fetchall()
    logFC.info(f"'test' listBooks = {listBooks}")

    # listBooks = result.scalars().all()
    return listBooks  # db_json(listB)
