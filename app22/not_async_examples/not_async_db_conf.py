from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app22.core.config import DATABASE_URL


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
