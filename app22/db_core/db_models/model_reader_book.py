from __future__ import annotations

from sqlalchemy import (
    Column,
    Integer,
    String,
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
    from app22.db_core.db_models.model_reader_assoc import ListBookAssociation


class Reader(Base):
    __tablename__ = "readers"

    id = Column(Integer(), primary_key=True)

    nickname = Column(String(30), nullable=False, unique=True)
    user_id = Column(Integer(), default=0, nullable=False)

    # association between Reader -> ListBook = ForeignKey('readers.id',
    book_lists: Mapped[list["ListBook"]] = relationship(
        "ListBook",
        back_populates="reader",
        cascade="all, delete",
    )

    def __repr__(self):
        return (
            f"Reader["
            f"id={self.id}, "
            f"nickname='{self.nickname}', "
            # f"user_id={self.user_id}"
            f"]"
        )


class ListBook(Base):
    __tablename__ = "listbooks"
    __table_args__ = (UniqueConstraint("reader_id", "list_name", name="idx_unique_reader_list"),)

    id = Column(Integer(), primary_key=True)

    time_created: Mapped[time_stamp_utc]

    list_name = Column(String(30), nullable=False)
    description = Column(String(200), nullable=False)

    # association ForeignKey between ListBook -> Reader
    reader_id = Column(
        Integer(),
        ForeignKey("readers.id", ondelete="CASCADE"),
        nullable=False,
    )
    reader: Mapped["Reader"] = relationship(
        "Reader",
        back_populates="book_lists",
    )

    # association many to many -> ListBookAssociation(ForeignKey('books.id',
    books: Mapped[list["Book"]] = relationship(
        "Book",
        secondary="list_book_association",
        back_populates="lists",
    )

    # association between ListBook -> ListBookAssociation = ForeignKey('listbooks.id',
    book_associations: Mapped[list["ListBookAssociation"]] = relationship(
        back_populates="list_book",
        cascade="all, delete",
        overlaps="books",
    )

    def __repr__(self):
        return (
            f"ListBook["
            f"id={self.id}, "
            f"name='{self.list_name}', "
            f"reader_id={self.reader_id}, "
            # f"time_created={self.time_created}, "
            # f"description={self.description}"
            f"]"
        )


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer(), primary_key=True)

    title = Column(String(50), nullable=False)
    description = Column(String(200), nullable=False)
    author = Column(String(50), nullable=False)

    # association between Book -> Category = BookCategoryAssociation(ForeignKey('books.id',
    categories: Mapped[list["Category"]] = relationship(
        "Category",
        secondary="book_category_association",
        back_populates="books",
    )

    # association many to many-> ListBookAssociation(ForeignKey('listbooks.id',
    lists: Mapped[list["ListBook"]] = relationship(
        "ListBook",
        secondary="list_book_association",
        back_populates="books",
        overlaps="book_associations",
    )

    # association between Book -> ListBookAssociation = ForeignKey('books.id',
    list_associations: Mapped[list["ListBookAssociation"]] = relationship(
        back_populates="book",
        cascade="all, delete",
        overlaps="books,lists",
    )

    def __repr__(self):
        return (
            f"Book["
            # f"id={self.id}, "
            f"title='{self.title}', "
            # f"description={self.description}, "
            # f"author={self.author}"
            f"]"
        )


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer(), primary_key=True)

    genre = Column(String(30), nullable=False)
    description = Column(String(200), nullable=False)

    # association between Category -> Book = BookCategoryAssociation(ForeignKey('categories.id'),
    books: Mapped[list["Book"]] = relationship(
        "Book",
        secondary="book_category_association",
        back_populates="categories",
    )

    def __repr__(self):
        return (
            f"Category["
            f"id={self.id}, "
            f"genre='{self.genre}', "
            # f"description={self.description}"
            f"]"
        )
