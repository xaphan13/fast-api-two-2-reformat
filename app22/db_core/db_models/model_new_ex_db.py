from __future__ import annotations

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
)

from sqlalchemy.orm import (
    Mapped,
    relationship,
)

from app22.db_core.base import Base
from app22.db_core.db_models.type_for_models import time_stamp_utc


class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    nickname = Column(String(20), unique=True)
    email = Column(String(40), unique=True)

    firstname = Column(String(20), nullable=True)
    surname = Column(String(20), nullable=True)
    password = Column(String(100))

    posts = relationship(
        "Post",
        back_populates="author",
        lazy="select",
        cascade="all, delete",
    )

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, username={self.nickname!r}, email={self.email})"


class Post(Base):
    __tablename__ = "posts"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    time_created: Mapped[time_stamp_utc]

    title = Column(String())
    content = Column(String())

    user_id = Column(
        Integer(),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        nullable=False,
    )

    author = relationship(
        "User",
        back_populates="posts",
    )

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(id={self.id}, title={self.title!r}, "
            f"user_id={self.user_id}, time_created={self.time_created})"
        )
