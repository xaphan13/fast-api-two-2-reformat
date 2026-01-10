from sqlalchemy.ext.asyncio import AsyncSession
from app22.db_crud_base.async_crud_base import AsyncBaseCRUD, ReaderType, SqlType

from app22.db_core.db_models.model_new_ex_db import User, Post
from app22.async_join_tables.schema_user_post import CreateUser, GetUser, CreatePost
from sqlalchemy import Column
from sqlalchemy.sql import select
from sqlalchemy.orm import selectinload


class UserAsyncCRUD(AsyncBaseCRUD[User, CreateUser, GetUser, CreateUser, GetUser]):
    # ==========================================================================
    # +++++++++ User -> posts=relationship[Post] - selectinload(Post) ++++++++++
    # --------------------------------------------------------------------------
    async def get_user_posts_one(self, schema: ReaderType, db: AsyncSession) -> SqlType | None:
        filter_attr = self._get_filter_attr(schema)
        query = select(self.model).where(*filter_attr).options(selectinload(self.model.posts))
        # ___________________ await  async  select  one ____________________
        return await self.get_record_one(schema, db, query_n=query)

    async def get_users_posts_list(self, schema: ReaderType, db: AsyncSession) -> list[SqlType]:
        filter_attr = self._get_filter_attr(schema)
        query = select(self.model).where(*filter_attr).options(selectinload(self.model.posts))
        # ___________________ await  async  select  all ____________________
        return await self.get_records_list(schema, db, query_n=query)

    async def get_all_users_posts(self, order_by: list[Column[SqlType]], db: AsyncSession) -> list[SqlType]:
        query = select(self.model).order_by(*order_by).options(selectinload(self.model.posts))
        # ___________________ await  async  select  all ____________________
        return await self.get_all_records(order_by, db, query_n=query)

    # ==========================================================================
    # +++++++++++++ User -> posts=List[Post] - posts.append(Post) ++++++++++++++
    # --------------------------------------------------------------------------
    async def add_post_user(self, schema: CreatePost, user: User, db: AsyncSession, commit: bool = True) -> Post:
        new_post: Post = Post(**schema.model_dump())
        user.posts.append(new_post)
        # ______________________ await  async  added _______________________
        if commit:
            await db.commit()
            await db.refresh(new_post)
        return new_post


userDB = UserAsyncCRUD(User)
