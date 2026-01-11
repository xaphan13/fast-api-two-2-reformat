from __future__ import annotations

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    UniqueConstraint,
)

from sqlalchemy.orm import (
    Mapped,
    relationship,
)

from app22.db_core.base import Base
from app22.db_core.db_models.type_for_models import time_stamp_utc

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app22.db_core.db_models.model_reader_book import ListBook, Book


class ListBookAssociation(Base):
    __tablename__ = "list_book_association"
    __table_args__ = (UniqueConstraint("list_id", "book_id", name="idx_unique_list_book"),)

    id = Column(
        Integer(),
        primary_key=True,
    )

    time_add: Mapped[time_stamp_utc]

    # association secondary between Association -> ListBook
    list_id = Column(
        Integer(),
        ForeignKey("listbooks.id", ondelete="CASCADE"),
        nullable=False,
    )

    # association secondary between Association -> Book
    book_id = Column(
        Integer(),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
    )

    list_book: Mapped["ListBook"] = relationship(
        "ListBook",
        back_populates="book_associations",
        overlaps="books,lists",
    )

    book: Mapped["Book"] = relationship(
        "Book",
        back_populates="list_associations",
        overlaps="books,lists",
    )

    def __repr__(self):
        return (
            f"ListBookAssociation(id={self.id}, time_add={self.time_add}, "
            f"list_id={self.list_id}, book_id={self.book_id})"
        )


class BookCategoryAssociation(Base):
    __tablename__ = "book_category_association"
    __table_args__ = (UniqueConstraint("category_id", "book_id", name="idx_unique_category_book"),)

    id = Column(
        Integer(),
        primary_key=True,
    )

    # association secondary between Association -> Book
    book_id = Column(
        Integer(),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
    )

    # association secondary between Association -> Category
    category_id = Column(
        Integer(),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
    )

    def __repr__(self):
        return f"BookCategoryAssociation(id={self.id}, book_id={self.book_id}, category_id={self.category_id})"
