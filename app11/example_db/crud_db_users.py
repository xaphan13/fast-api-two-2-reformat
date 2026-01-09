from typing import Optional
from fastapi import Depends, HTTPException
from sqlalchemy import and_, select, Row, Result, insert
from sqlalchemy.orm import Session

from app11.db_core.db_conf import SessionDB
from app11.example_db.model_ex_db import User
from app11.example_db.schema_ex_db import GetUserQuery, UserCreateBody


# Depends - requesting user from the database *******************************************
def dep_getUser_id(user_id: int, db: Session = Depends(SessionDB.get_db)) -> Optional[User]:
    user: Optional[User] = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=422, detail=f"User with id={user_id} not found")
    return user


def dep_getUser_name(nickname: str, db: Session = Depends(SessionDB.get_db)) -> Optional[User]:
    user: Optional[User] = db.query(User).filter(User.nickname == nickname).first()
    if user is None:
        raise HTTPException(status_code=422, detail=f"User with nickname={nickname} not found")
    return user


# requesting user from the database *****************************************************
def crud_query_filterby_getUser(db: Session, **kwargs) -> Optional[User]:
    return db.query(User).filter_by(**kwargs).first()


# ***************************************************************************************
# example crud ==========================================================================
# ---------------------------------------------------------------------------------------
def crud_select_where_getUser(db: Session, **query_dict) -> Optional[User]:
    filter_conditions = []
    for key, value in query_dict.items():
        filter_conditions.append(getattr(User, key) == value)

    if filter_conditions:
        dynamic_filter = and_(*filter_conditions)
        return db.scalar(select(User).where(dynamic_filter))
    return None


def example_execute_select_getUser(db: Session, query: GetUserQuery) -> Optional[User]:
    res_user: Result[User] = db.execute(select(User).where(and_(User.id == query.id, User.nickname == query.nickname)))
    user_row: Row | None = res_user.fetchone()
    if user_row is not None:
        return user_row[0]
    return None


def example_execute_scalars_getUser(db: Session, query: GetUserQuery) -> Optional[User]:
    stmt = select(User).where(and_(User.id == query.id, User.nickname == query.nickname))
    user: Optional[User] = db.execute(stmt).scalars().first()
    if user is not None:
        return user
    return None


def crud_insert_user(body: UserCreateBody, db: Session) -> User:
    insert_stmt = insert(User).values(**body.dict())
    db.scalar(insert_stmt)
    db.commit()
    new_user: User = User(**body.dict(), id=-1)
    return new_user
