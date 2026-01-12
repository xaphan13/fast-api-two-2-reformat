__all__ = ("Base",)


from app22.db_core.base import Base


# """this is so that alembic can see the models and create tables"""
from app22.async_join_tables import model_new_ex_db
from app22.async_join_tables import model_join
from app22.async_join_tables import model_admin

from app22.async_many_sql import model_new_many_db

from app22.async_reader_project import model_reader_book
from app22.async_reader_project import model_reader_assoc


def get_models():
    """this is so that alembic can see the models and create tables"""
    return (
        # tables for app22.async_join_tables
        model_new_ex_db.User,
        model_new_ex_db.Post,
        model_join.JoinPerson,
        model_join.JoinAddress,
        model_admin.Admin_list,
        model_admin.Admin_work,
        # tables many to many - for app22.async_many_sql
        model_new_many_db.Order,
        model_new_many_db.Product,
        model_new_many_db.OrderProductAssociation,
        # tables association - for app22.async_reader_project
        model_reader_book.Reader,
        model_reader_book.ListBook,
        model_reader_book.Book,
        model_reader_book.Category,
        model_reader_assoc.ListBookAssociation,
        model_reader_assoc.BookCategoryAssociation,
    )
