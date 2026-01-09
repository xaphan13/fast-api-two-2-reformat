from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from datetime import datetime

from app22.db_core.base import Base
from app22.db_core.model.model_reader_assoc import ListBookAssociation, BookCategoryAssociation


class Reader(Base):
    __tablename__ = "readers"

    id = Column(Integer(), primary_key=True)

    nickname = Column(String(30), nullable=False)
    user_id = Column(Integer(), default=0, nullable=False)

    # association between Reader -> ListBook = ForeignKey('readers.id',
    book_lists = relationship("ListBook", back_populates="reader", cascade="all, delete")

    def __repr__(self):
        return f"Reader(id={self.id}, nickname={self.nickname}, user_id={self.user_id})"


class ListBook(Base):
    __tablename__ = "listbooks"

    id = Column(Integer(), primary_key=True)
    time_created = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=func.now())

    list_name = Column(String(30), nullable=False)
    description = Column(String(200), nullable=False)

    # association ForeignKey between ListBook -> Reader
    reader_id = Column(Integer(), ForeignKey("readers.id", ondelete="CASCADE"), nullable=False)
    reader = relationship("Reader", back_populates="book_lists")

    # association many to many -> ListBookAssociation(ForeignKey('books.id',
    books = relationship("Book", secondary=ListBookAssociation.__tablename__, back_populates="lists")

    # association between ListBook -> ListBookAssociation = ForeignKey('listbooks.id',
    book_associations = relationship("ListBookAssociation", back_populates="list_book", cascade="all, delete")

    def __repr__(self):
        return (
            f"ListBook(id={self.id}, list_name={self.list_name}, reader_id={self.reader_id}, "
            f"time_created={self.time_created}, description={self.description})"
        )


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer(), primary_key=True)

    title = Column(String(50), nullable=False)
    description = Column(String(200), nullable=False)
    author = Column(String(50), nullable=False)

    # association between Book -> Category = BookCategoryAssociation(ForeignKey('books.id',
    categories = relationship("Category", secondary=BookCategoryAssociation.__tablename__, back_populates="books")

    # association many to many-> ListBookAssociation(ForeignKey('listbooks.id',
    lists = relationship("ListBook", secondary=ListBookAssociation.__tablename__, back_populates="books")

    # association between Book -> ListBookAssociation = ForeignKey('books.id',
    list_associations = relationship("ListBookAssociation", back_populates="book", cascade="all, delete")

    def __repr__(self):
        return f"Book(id={self.id}, title={self.title}, description={self.description}, author={self.author})"


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer(), primary_key=True)

    genre = Column(String(30), nullable=False)
    description = Column(String(200), nullable=False)

    # association between Category -> Book = BookCategoryAssociation(ForeignKey('categories.id'),
    books = relationship("Book", secondary=BookCategoryAssociation.__tablename__, back_populates="categories")

    def __repr__(self):
        return f"Category(id={self.id}, genre={self.genre}, description={self.description})"
