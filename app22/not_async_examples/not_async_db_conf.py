from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app22.core.config import DATABASE_URL

# """this is so that alembic can see the models and create tables"""
from app22.async_join_tables import model_new_ex_db
from app22.async_join_tables import model_join
from app22.async_join_tables import model_admin
from app22.async_many_sql import model_new_many_db
from app22.async_reader_project import model_reader_book
from app22.async_reader_project import model_reader_assoc
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
            model_new_ex_db.User,
            model_new_ex_db.Post,
            model_join.JoinPerson,
            model_join.JoinAddress,
            model_admin.Admin_list,
            model_admin.Admin_work,
            # many to many
            model_new_many_db.Order,
            model_new_many_db.Product,
            model_new_many_db.OrderProductAssociation,
            # table association
            model_reader_book.Reader,
            model_reader_book.ListBook,
            model_reader_book.Book,
            model_reader_book.Category,
            model_reader_assoc.ListBookAssociation,
            model_reader_assoc.BookCategoryAssociation,
        )

    @staticmethod
    def get_db_not_async():
        """Dependency for getting session"""
        db = SessionDB_not_async.sessionLocal()
        try:
            yield db
        finally:
            db.close()

    @staticmethod
    def get_session():
        return SessionDB_not_async.sessionLocal()
