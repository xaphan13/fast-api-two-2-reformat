from sqlalchemy.ext.asyncio import AsyncSession

from app22.async_join_tables.schema_user_post import (
    CreatePost,
    GetPost,
)

from app22.async_join_tables.model_new_ex_db import (
    Post,
    User,
)

from app22.db_core.async_crud_base import (
    AsyncBaseCRUD,
    CreateType,
    SqlType,
)


class PostAsyncCRUD(AsyncBaseCRUD[Post, CreatePost, GetPost, GetPost, GetPost]):
    # ==========================================================================
    # ++++++++++++ Post -> author=relationship[User] - author=User +++++++++++++
    # --------------------------------------------------------------------------
    async def add_post_user(self, schema: CreateType, user: User, db: AsyncSession, commit: bool = True) -> SqlType:
        new_record: SqlType = self.model(**schema.model_dump(), author=user)
        db.add(new_record)
        # ______________________ await  async  added _______________________
        if commit:
            await db.commit()
            await db.refresh(new_record)
        return new_record


postDB = PostAsyncCRUD(Post)
