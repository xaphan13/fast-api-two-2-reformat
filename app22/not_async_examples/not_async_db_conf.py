from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app22.core.config import DATABASE_URL

# """this is so that alembic can see the models and create tables"""
from app22.async_join_tables.model_admin import *
from app22.async_join_tables.model_join import *
from app22.async_join_tables.model_new_ex_db import *
from app22.async_many_sql.model_new_many_db import *
from app22.async_reader_project.model_reader_book import *
from app22.async_reader_project.model_reader_assoc import *
from app22.db_core.base import Base


class SessionDB_not_async:
    """methods for working with the database"""

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        echo=True,
    )

    sessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
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

    @staticmethod
    def get_db_alembic():
        """Dependency for getting session"""
        db = SessionDB_not_async.sessionLocal()
        try:
            yield db
        finally:
            db.close()

    @staticmethod
    def get_session():
        return SessionDB_not_async.sessionLocal()
