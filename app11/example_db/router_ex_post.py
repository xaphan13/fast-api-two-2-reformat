from fastapi import APIRouter, Depends, HTTPException
from typing import Type, Any, Optional

from app11.db_core.base import Base
from app11.db_core.db_conf import SessionDB
from sqlalchemy.orm import Session
from sqlalchemy import Column, text

from app11.example_db.except_ex_db import MyApiRouter
from app11.example_db.schema_ex_db import (
    PostSchemaResp,
    GetPostQuery,
    PostSchemaAuthorResp,
    PostCreateBody,
    PostsOrderQuery,
    PostUpdateBody,
    MigrationUpdateBody,
)

from app11.example_db.crud_db_users import dep_getUser_id, dep_getUser_name
from app11.example_db.model_ex_db import Post, User


from app11.config_log import ConfigLogger

logFC = ConfigLogger.get_logger("FileStdout")


ex_post_route = APIRouter(route_class=MyApiRouter, prefix="/ex_post", tags=["ex_post"])


# UPDATE alembic version_num in database **********************************************************
@ex_post_route.put("/update_migration", response_model=dict)
def update_migration(body: MigrationUpdateBody, db: Session = Depends(SessionDB.get_db)):
    current_version: Optional[str] = db.execute(text("SELECT version_num FROM alembic_version")).scalar()
    logFC.info(f"update_migration : {current_version=}")

    if current_version is None:
        raise HTTPException(status_code=404, detail="Current migration version not found")

    try:
        db.execute(text("UPDATE alembic_version SET version_num = :new_version"), {"new_version": body.new_version})
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update migration version: {e}")

    logFC.info(f"Migration version updated : {body.new_version=}")
    return {"message": "Migration version updated", "new_version": body.new_version}


# adding users to the database **********************************************************
@ex_post_route.post("/add_post_userid", response_model=PostSchemaAuthorResp, status_code=200)
def add_post_userid(
    body: PostCreateBody, db: Session = Depends(SessionDB.get_db), user: User = Depends(dep_getUser_id)
):
    new_post: Post = Post(title=body.title, content=body.content, user_id=user.id)
    db.add(new_post)
    db.commit()
    return new_post


@ex_post_route.post("/add_post_nickname", response_model=PostSchemaAuthorResp, status_code=200)
def add_post_nickname(
    body: PostCreateBody, db: Session = Depends(SessionDB.get_db), user: User = Depends(dep_getUser_name)
):
    new_post: Post = Post(**body.dict(exclude={"nickname"}))
    new_post.author = user
    db.add(new_post)
    db.commit()
    return new_post


@ex_post_route.post("/add_post_append", response_model=PostSchemaAuthorResp, status_code=200)
def add_post_append(
    body: PostCreateBody, db: Session = Depends(SessionDB.get_db), user: User = Depends(dep_getUser_name)
):
    new_post: Post = Post(title=body.title, content=body.content)
    user.posts.append(new_post)
    db.add(new_post)
    db.commit()
    return new_post


# requesting post from the database ****************************************************
@ex_post_route.get("/get_post", response_model=PostSchemaResp, status_code=200)
def get_post(query: GetPostQuery = Depends(), db: Session = Depends(SessionDB.get_db)):
    query_dict = {key: value for key, value in query.dict().items() if value is not None}
    post = db.query(Post).filter_by(**query_dict).first()

    if post:
        return post
    raise HTTPException(status_code=500, detail=f"Post with {query_dict} not found")


# requesting list of posts from the database ****************************************************
@ex_post_route.get("/get_posts_all_order_by", response_model=list[PostSchemaResp], status_code=200)
def get_posts_all_order_by(order: PostsOrderQuery, db: Session = Depends(SessionDB.get_db)):
    order_first: Column[Any] = Post.id
    order_sec: Column[Any] = Post.title

    if order == "time":
        order_first, order_sec = Post.time_created, Post.title
    elif order == "title":
        order_first, order_sec = Post.title, Post.id
    elif order == "user_id":
        order_first, order_sec = Post.user_id, Post.time_created

    posts: list[Type[Post]] = db.query(Post).order_by(order_first).order_by(order_sec).all()
    return posts


@ex_post_route.get("/get_posts_all_author", response_model=list[PostSchemaAuthorResp], status_code=200)
def get_posts_all_author(db: Session = Depends(SessionDB.get_db)):
    posts: list[Type[Post]] = db.query(Post).join(User).order_by(User.nickname).all()
    return posts


# deleting post from the database *****************************************************
@ex_post_route.delete("/delete_post", response_model=PostSchemaResp)
def delete_user(query: GetPostQuery = Depends(), db: Session = Depends(SessionDB.get_db)):
    query_dict = {key: value for key, value in query.dict().items() if value is not None}
    post = db.query(Post).filter_by(**query_dict).first()
    if post is None:
        raise HTTPException(status_code=500, detail=f"Post with {query_dict} not found")

    db.delete(post)
    db.commit()
    return post


# updating post from the database *****************************************************
@ex_post_route.put("/update_post", response_model=PostSchemaResp)
def update_post(body: PostUpdateBody, db: Session = Depends(SessionDB.get_db)):
    post: Optional[Post] = db.query(Post).filter(Post.id == body.id).first()
    if post is None:
        raise HTTPException(status_code=422, detail=f"Post with id={body.id} not found")

    for name, value in body.dict(exclude_unset=True, exclude={"id"}).items():
        if value != "":
            setattr(post, name, value)

    db.commit()
    return post


# requesting post from the database ****************************************************
@ex_post_route.get("/drop_all_tables", status_code=200)
def drop_all_tables(db: Session = Depends(SessionDB.get_db)):
    # User.__table__.drop(db.bind, checkfirst=True)
    # Post.__table__.drop(db.bind, checkfirst=True)
    Base.metadata.drop_all(bind=db.bind)
    return 0


# ***************************************************************************************
# templates requesting posts to dataBase ================================================
# ---------------------------------------------------------------------------------------
@ex_post_route.get("/template_posts_joinedload", response_model=list[PostSchemaAuthorResp], status_code=200)
def template_posts_joinedload(db: Session = Depends(SessionDB.get_db)):
    # posts: list[Type[Post]] = db.query(Post).outerjoin(Post.author).order_by(User.nickname).all()

    posts: list[Type[Post]] = db.query(Post).join(User).order_by(User.nickname).all()
    # posts: list[Type[Post]] = db.query(Post).join(User)  \
    #                             .options(selectinload(Post.author))  \
    #                             .order_by(User.nickname).all()
    # posts: list[Type[Post]] = db.query(Post).join(User) \
    #                             .options(joinedload(Post.author)) \
    #                             .order_by(User.nickname).all()

    return posts  # joinedload  or selectinload
