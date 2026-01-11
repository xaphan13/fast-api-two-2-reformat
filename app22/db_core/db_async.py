from typing import Any, AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    async_scoped_session,
)

from asyncio import current_task

from app22.core.config import DATABASE_URL_ASYNC

# """this is so that alembic can see the models and create tables"""
from app22.async_join_tables.model_admin import *
from app22.async_join_tables.model_join import *
from app22.async_join_tables.model_new_ex_db import *
from app22.async_many_sql.model_new_many_db import *
from app22.async_reader_project.model_reader_book import *
from app22.async_reader_project.model_reader_assoc import *
from app22.db_core.base import Base


class AsyncSessionDB:
    def __init__(self, url: str, echo: bool = False):
        self.async_engine = create_async_engine(
            url,
            echo=echo,
            future=True,
        )

        self.async_session = async_sessionmaker(
            bind=self.async_engine,
            autoflush=False,
            expire_on_commit=False,
        )

        self.async_scoped = async_scoped_session(
            session_factory=self.async_session,
            scopefunc=current_task,
        )

    @staticmethod
    def get_models():
        """this is so that alembic can see the models and create tables"""
        return (
            Base,
            User,
            Post,
            JoinPerson,
            JoinAddress,
            Order,
            Product,
            OrderProductAssociation,
            Admin_list,
            Admin_work,
            Reader,
            ListBook,
            Book,
            Category,
            ListBookAssociation,
            BookCategoryAssociation,
        )

    async def get_db(self) -> AsyncGenerator[AsyncSession, Any]:
        """Dependency for getting session"""
        session: AsyncSession = self.async_session()
        try:
            yield session
        finally:
            await session.close()

    def get_session(self) -> AsyncSession:
        return self.async_session()

    async def scop_db(self) -> AsyncGenerator[AsyncSession, Any]:
        """Dependency for getting session"""
        session: AsyncSession = self.async_scoped()
        try:
            yield session
        finally:
            await session.close()


async_db = AsyncSessionDB(url=DATABASE_URL_ASYNC, echo=True)
