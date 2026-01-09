from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func
from datetime import datetime
from app22.db_core.base import Base


class TableName(Base):
    __tablename__ = "tablename"

    id = Column(Integer(), primary_key=True, index=True)
    time_created = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=func.now())

    name = Column(String(20))
    surname = Column(String(20))
    addr_id = Column(Integer(), default=0)

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, name={self.name}, surname={self.surname})"
