from __future__ import annotations

from decimal import Decimal
from typing import Self

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    username: Mapped[str] = mapped_column(
        String(length=50), nullable=False, unique=True
    )
    email: Mapped[str] = mapped_column(String(length=120), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(length=200), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(
        String, default="buyer", nullable=False, index=True
    )
    # TODO: for now this is `buyer` or `seller` or `admin`, refactor to
    # `Enum(UserRole)` where `UserRole` is:
    # class UserRole(Enum):
    #     buyer: auto()
    #     seller: auto()
    #     abmind: auto()

    products: Mapped[list[Product]] = relationship(
        "Product", back_populates="seller", cascade="all, delete-orphan"
    )


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(length=50), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True
    )
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=True, index=True
    )

    parent: Mapped[Self | None] = relationship(
        "Category", back_populates="children", remote_side="Category.id"
    )
    children: Mapped[list[Self]] = relationship("Category", back_populates="parent")
    products: Mapped[list[Product]] = relationship(
        "Product", back_populates="category", cascade="all, delete-orphan"
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(length=100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(length=500), nullable=True)
    price: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2), nullable=False
    )
    image_url: Mapped[str | None] = mapped_column(String(length=200), nullable=True)
    stock: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=False, index=True
    )
    seller_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )

    category: Mapped[Category] = relationship("Category", back_populates="products")
    seller: Mapped[User] = relationship("User", back_populates="products")
