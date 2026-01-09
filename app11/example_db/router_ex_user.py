from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, Type, Sequence

from app11.db_core.db_conf import SessionDB
from sqlalchemy import select, ScalarResult, Row, update, and_
from sqlalchemy.orm import Session

from app11.example_db.except_ex_db import MyApiRouter
from app11.example_db.schema_ex_db import (
    UserCreateBody,
    UserSchemaResp,
    GetUserQuery,
    UserSchemaPostsResp,
    UserUpdateBody,
)

from app11.example_db.crud_db_users import (
    crud_select_where_getUser,
    crud_query_filterby_getUser,
    example_execute_select_getUser,
    example_execute_scalars_getUser,
    dep_getUser_name,
)

from app11.example_db.model_ex_db import User, Post


ex_user_route = APIRouter(route_class=MyApiRouter, prefix="/ex_user", tags=["ex_user"])


# adding users to the database **********************************************************
@ex_user_route.post("/add_user", response_model=UserSchemaResp, status_code=200)
def add_user(body: UserCreateBody, db: Session = Depends(SessionDB.get_db)):
    new_user: User = User(**body.dict())
    db.add(new_user)
    db.commit()
    return new_user


@ex_user_route.post("/add_users_list", response_model=list[UserSchemaResp], status_code=200)
def add_users_list(body_list: list[UserCreateBody], db: Session = Depends(SessionDB.get_db)):
    users_list: list[User] = [User(**body_user.dict()) for body_user in body_list]
    db.add_all(users_list)
    db.commit()
    return users_list


# requesting user from the database *****************************************************
@ex_user_route.get("/get_user_filterby", response_model=UserSchemaResp, status_code=200)
def get_user_filterby(query: GetUserQuery = Depends(), db: Session = Depends(SessionDB.get_db)):
    query_dict = {key: value for key, value in query.dict().items() if value is not None}
    user: Optional[User] = crud_query_filterby_getUser(db, **query_dict)

    if user:
        return user
    raise HTTPException(status_code=422, detail=f"User with {query_dict} not found")


@ex_user_route.get("/get_user_posts", response_model=UserSchemaPostsResp, status_code=200)
def get_user_posts(query: GetUserQuery = Depends(), db: Session = Depends(SessionDB.get_db)):
    query_dict = {key: value for key, value in query.dict().items() if value is not None}
    user: Optional[User] = db.query(User).filter_by(**query_dict).first()

    if user:
        return user
    raise HTTPException(status_code=422, detail=f"User with {query_dict} not found")


# requesting list of users from the database ********************************************
@ex_user_route.get("/get_users_list_query", response_model=list[UserSchemaResp], status_code=200)
def get_users_list_query(db: Session = Depends(SessionDB.get_db)):
    users: list[Type[User]] = db.query(User).order_by(User.id).order_by(User.nickname).all()
    return users


@ex_user_route.get("/get_users_posts_list", response_model=list[UserSchemaPostsResp], status_code=200)
def get_users_posts_list(db: Session = Depends(SessionDB.get_db)):
    users: list[Type[User]] = db.query(User).order_by(User.id).order_by(User.nickname).all()
    return users


# deleting user from the database *****************************************************
@ex_user_route.delete("/delete_user", response_model=UserSchemaResp)
def delete_user(db: Session = Depends(SessionDB.get_db), user: User = Depends(dep_getUser_name)):
    db.delete(user)
    db.commit()
    return user


# updating user from the database *****************************************************
@ex_user_route.put("/update_user", response_model=UserSchemaResp)
def update_user(body: UserUpdateBody, db: Session = Depends(SessionDB.get_db), user: User = Depends(dep_getUser_name)):
    for name, value in body.dict(exclude_unset=True).items():
        if value != "":
            setattr(user, name, value)

    db.commit()
    return user


# ***************************************************************************************
# templates requesting users to dataBase ================================================
# ---------------------------------------------------------------------------------------
@ex_user_route.put("/template_update_user", response_model=UserSchemaResp)
def template_update_user(
    body: UserUpdateBody, db: Session = Depends(SessionDB.get_db), user: User = Depends(dep_getUser_name)
):
    query_dict = {key: value for key, value in body.dict(exclude_unset=True).items() if value != ""}

    stmt = update(User).where(User.id == int(user.id)).values(query_dict).returning(User.id)

    # res_update = db.execute(stmt).scalars().first()
    res_update = db.scalar(stmt)
    db.commit()
    print(f"res_update = {res_update} - {user.id} - \n{stmt}")

    return user


@ex_user_route.get("/template_get_user", response_model=UserSchemaResp, status_code=200)
def template_get_user(
    type_sql: int = Query(2), query: GetUserQuery = Depends(), db: Session = Depends(SessionDB.get_db)
):
    user: Optional[User] = None
    query_dict = {key: value for key, value in query.dict().items() if value is not None}

    if type_sql == 2:
        user = crud_select_where_getUser(db, **query_dict)
    if type_sql == 3:
        user = db.query(User).filter(User.nickname == query.nickname).first()
    if type_sql == 4:
        user = db.query(User).filter_by(**query_dict).first()
    if type_sql == 5:
        user = db.scalar(select(User).where(User.nickname == query.nickname))
    if type_sql == 6:
        user = example_execute_select_getUser(db, query)
    if type_sql == 7:
        user = example_execute_scalars_getUser(db, query)

    if user:
        return user
    raise HTTPException(status_code=422, detail=f"User with {query_dict} not found")


@ex_user_route.get("/template_get_users_list", response_model=list[UserSchemaResp], status_code=200)
def template_get_users_list(type_sql: int = Query(1), db: Session = Depends(SessionDB.get_db)):
    users = []
    stmt = select(User).order_by(User.id).order_by(User.nickname)

    if type_sql == 1:
        users: list[Type[User]] = db.query(User).order_by(User.id).order_by(User.nickname).all()
    if type_sql == 2:
        users: ScalarResult[User] = db.scalars(stmt)
    if type_sql == 3:
        users: ScalarResult[User] = db.execute(stmt).scalars()
    if type_sql == 4:
        users: Sequence[User] = db.execute(stmt).scalars().all()
    if type_sql == 5:
        result = db.execute(stmt)
        users_row_list: Sequence[Row[User]] = result.fetchall()
        users = [user_row[0] for user_row in users_row_list]

    return users


@ex_user_route.get("/template_query", response_model=UserSchemaResp, status_code=200)
def template_query(query: GetUserQuery = Depends(), db: Session = Depends(SessionDB.get_db)):
    user1 = db.query(User.email).filter_by(id=query.id, nickname=query.nickname).first()
    print(f"\n\n template_query 1 = {type(user1)} = {user1}")

    user21 = db.query(User, Post).outerjoin(Post).where(and_(User.id == query.id, Post.user_id == query.id)).first()
    print(f"\n\n template_query 21 = {type(user21[0])} = {user21}")

    user22 = db.query(User, Post).join(Post).where(and_(User.id == query.id, Post.user_id == query.id)).all()
    print(f"\n\n template_query 22 = {type(user22[0][1])} = {user22}")

    user3 = db.query(User).filter(and_(User.id == query.id, User.nickname == query.nickname)).first()
    print(f"\n\n template_query 3 = {user3}")

    filter_conditions = [getattr(User, key) == value for key, value in query.dict(exclude_none=True).items()]
    dynamic_filter = and_(*filter_conditions)
    user4 = db.query(User).where(dynamic_filter).first()
    print(f"\n\n template_query 4 = {user4}")

    if user4:
        return user4
    raise HTTPException(status_code=422, detail=f"User with {query.nickname} not found")
