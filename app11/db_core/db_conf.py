from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app11.core.config import DATABASE_URL

# """this is so that alembic can see the models and create tables"""
from app11.run_task.model_task import *
from app11.example_many_db.model_many_db import *
from app11.example_db.model_ex_db import *
from app11.db_core.base import Base


class SessionDB:
    """methods for working with the database"""

    # """URL в файле config.py"""
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=True)

    # """будет использоваться для создания сессий базы данных"""
    sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    @staticmethod
    def get_models():
        """this is so that alembic can see the models and create tables"""
        return Base, TaskOne, TaskTwo, Post, User, Order, Product, OrderProductAssociation

    @staticmethod
    def get_db():
        """Dependency for getting session"""
        db = SessionDB.sessionLocal()
        try:
            yield db
        finally:
            db.close()

    @staticmethod
    def get_session():
        return SessionDB.sessionLocal()
