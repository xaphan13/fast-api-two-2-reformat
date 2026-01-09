from app22.logger_core.config_logger import ConfigLogger
from fastapi import APIRouter, Depends
from sqlalchemy.sql import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app22.db_core.db_async import async_db

from app22.join_tables.schema_join import CreateJoinPerson, GetJoinPerson, CreateJoinAddress, GetJoinAddress
from app22.join_tables.schema_user_post import CreateUser, CreatePost, GetUser, RespPost, GetPost

from app22.db_core.model.model_join import JoinPerson, JoinAddress
from app22.db_core.model.temp_admin import Admin_list, Admin_work
from app22.db_core.model.model_new_ex_db import User, Post

from app22.db_crud_base.async_join_address import addrDB
from app22.db_crud_base.async_join_person import personDB
from app22.db_crud_base.async_post import postDB
from app22.db_crud_base.async_user import userDB
from app22.new_routers.data_join import data_addr, data_pers


logFC = ConfigLogger.getLogger("FileStdout", "join_one_r")


join_one_r = APIRouter(prefix="/join_one_r", tags=["NEW join_one_r"])


# ==============================================================================
# +++++++++++++++++++ JoinPerson - select - JoinAddress ++++++++++++++++++++++++
# ------------------------------------------------------------------------------
@join_one_r.get("/add_user_post", response_model=RespPost | int)
async def add_user_post(action: int = 3, db: AsyncSession = Depends(async_db.get_db)):
    if action == 0:
        await userDB.delete_record_many(GetUser(), db)
        return 0
    if action == 1:
        postG: Post = await postDB.get_record_one(GetPost(content="content-11"), db)
        # await postDB.update_record_one(postG, GetPost(content="newUpdate"), db)
        await postDB.delete_record_one(postG, db)
        # await postDB.delete_record_many(GetPost(content="content-22"), db)
        return 0
    elif action == 2:
        await userDB.delete_record_many(GetUser(nickname="user123"), db)
    elif action == 3:
        await userDB.delete_record_many(GetUser(), db)

    if action != 4:
        userC: CreateUser = CreateUser(nickname="user123", email="user123@example.com", password="password123")
        await userDB.add_record(userC, db)

    userG: User = await userDB.get_user_posts_one(GetUser(nickname="user123"), db)
    if action == 4:
        logFC.info(f"posts = {len(userG.posts)} {userG.posts}")
        await postDB.update_record_one(userG.posts[0], GetPost(content="newUpdate0"), db)
        await postDB.update_record_one(userG.posts[2], GetPost(content="newUpdate1"), db)
        await postDB.delete_record_one(userG.posts[1], db)
        return -4

    post1 = CreatePost(title="Example Title1", content="content-11", user_id=userG.id)
    await postDB.add_record(post1, db)

    post2 = CreatePost(title="Example Title2", content="content-22")
    await postDB.add_post_user(post2, userG, db)

    post3 = CreatePost(title="Example Title31", content="content-33")
    post_add: Post = await userDB.add_post_user(post3, userG, db)

    return post_add


# ==============================================================================
# +++++++++++++++++++ JoinPerson - select - JoinAddress ++++++++++++++++++++++++
# ------------------------------------------------------------------------------
@join_one_r.get("/get_person", response_model=dict)
async def get_person(db: AsyncSession = Depends(async_db.get_db)):
    # stmt = (select(JoinPerson, JoinAddress)
    #         .outerjoin(JoinAddress, JoinAddress.addr_index == JoinPerson.link_addr))
    stmt = select(JoinPerson, JoinAddress).join(JoinAddress, JoinAddress.addr_index == JoinPerson.link_addr)
    # stmt = (select(JoinPerson, JoinAddress)
    #         .where(JoinAddress.addr_index == JoinPerson.link_addr))

    result = await db.execute(stmt)
    records = result.fetchall()

    for record in records:
        per = record.JoinPerson
        addr = record.JoinAddress
        logFC.info(f"result  {per} {addr}")

    return {}


# ______________________________________________________________________________


# ==============================================================================
# +++++++++++++++++ create_person_addr delete_person_addr ++++++++++++++++++++++
# ------------------------------------------------------------------------------
@join_one_r.post("/create_person_addr", response_model=dict)
async def create_person_addr(db: AsyncSession = Depends(async_db.get_db)):
    await personDB.delete_record_many(GetJoinPerson(), db)
    await addrDB.delete_record_many(GetJoinAddress(), db)

    for idx, city, street in data_addr:
        addr = CreateJoinAddress(
            addr_index=idx,
            city=city,
            street=street,
        )
        await addrDB.add_record(addr, db)

    for name, surname, link_addr in data_pers:
        person = CreateJoinPerson(
            name=name,
            surname=surname,
            link_addr=link_addr,
        )
        await personDB.add_record(person, db)
    return {"CreateJoinAddress": len(data_addr), "CreateJoinPerson": len(data_pers)}


# ******************* delete_person_addr to the database ***********************
@join_one_r.delete("/delete_person_addr", response_model=dict)
async def delete_person_addr(
    params_pers: GetJoinPerson = Depends(),
    params_addr: GetJoinAddress = Depends(),
    db: AsyncSession = Depends(async_db.get_db),
):
    qty_pers = await personDB.delete_record_many(params_pers, db)
    qty_addr = await addrDB.delete_record_many(params_addr, db)
    return {"DeleteJoinAddress": qty_addr, "DeleteJoinPerson": qty_pers}


# ______________________________________________________________________________


# ==============================================================================
# ++++++++++++++ Admin_list - admin_worked.append - Admin_work +++++++++++++++++
# ------------------------------------------------------------------------------
@join_one_r.post("/create_Admin_list", response_model=dict)
async def create_Admin_list(db: AsyncSession = Depends(async_db.get_db)):
    new_order: Admin_list = Admin_list(user_id="new1")
    db.add(new_order)
    await db.commit()
    return {}


@join_one_r.post("/fixing_work_admin", response_model=dict)
async def fixing_work_admin(db: AsyncSession = Depends(async_db.get_db)):
    admin_id_work: str = "new1"
    callback_data: str = "callback_data"

    stmt = (
        select(Admin_list)
        .options(selectinload(Admin_list.admin_worked))
        .where(Admin_list.user_id == str(admin_id_work))
    )

    admin_stmt = await db.execute(stmt)
    add_work: Admin_list = admin_stmt.scalar_one()
    logFC.info(f"fixing_work_admin  {add_work} {add_work.admin_id}")

    add_work.admin_worked.append(Admin_work(type_work="Registration", callback_data=callback_data))
    # add_work.admin_worked = [Admin_work(type_work='Registration', callback_data=callback_data)]

    # work = Admin_work(admin_id=add_work.admin_id, type_work='Registration', callback_data=callback_data)
    # work = Admin_work(admin_lists=add_work, type_work='Registration', callback_data=callback_data)
    # db.add(work)

    await db.commit()

    return {}


# ______________________________________________________________________________
