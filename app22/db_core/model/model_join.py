from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func
from datetime import datetime
from app22.db_core.base import Base


class JoinPerson(Base):
    __tablename__ = "joinperson"

    id = Column(Integer(), primary_key=True, index=True)
    time_created = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=func.now())

    name = Column(String(20))
    surname = Column(String(20))
    link_addr = Column(Integer(), default=-1)

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(id={self.id}, "
            f"name={self.name}, surname={self.surname}, link_addr={self.link_addr})"
        )


class JoinAddress(Base):
    __tablename__ = "joinaddress"

    id = Column(Integer(), primary_key=True, index=True)
    time_created = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=func.now())

    city = Column(String(20))
    street = Column(String(20))
    addr_index = Column(Integer(), default=0)

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(addr_index={self.addr_index}, "
            f"city={self.city}, street={self.street}, id={self.id})"
        )
