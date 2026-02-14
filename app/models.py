from __future__ import annotations

import enum
from datetime import UTC, datetime
from decimal import Decimal
from functools import partial
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserRole(enum.StrEnum):
    admin = "admin"
    seller = "seller"
    buyer = "buyer"


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
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, index=True)

    products: Mapped[list[Product]] = relationship(
        back_populates="seller", cascade="all, delete-orphan"
    )
    reviews: Mapped[list[Review]] = relationship(
        back_populates="reviewer", cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class UserBase(BaseModel):
    username: Annotated[str, Field(min_length=3, max_length=64)]
    email: Annotated[EmailStr, Field(max_length=120)]


class UserCreate(UserBase):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    password: Annotated[str, Field(max_length=8)]
    role: Literal[UserRole.seller, UserRole.buyer] = UserRole.buyer


class UserUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    password: str | None = None


class UserPublicBase(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class UserPublic(UserPublicBase):
    role: Literal[UserRole.seller, UserRole.buyer]


class UserPrivate(UserPublicBase):
    role: Literal[UserRole.seller, UserRole.buyer, UserRole.admin]


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    token: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    expired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )

    user: Mapped[User] = relationship(back_populates="refresh_tokens")


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class Token(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    access_token: str
    refresh_token: str
    token_type: str


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

    parent: Mapped[Category | None] = relationship(
        back_populates="children", remote_side="Category.id"
    )
    children: Mapped[list[Category]] = relationship(back_populates="parent")
    products: Mapped[list[Product]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )


class CategoryBase(BaseModel):
    name: Annotated[str, Field(min_length=3, max_length=50)]


class CategoryCreate(CategoryBase):
    parent_id: int | None = None
    is_active: bool | None = True


class CategoryUpdate(BaseModel):
    name: Annotated[str | None, Field(min_length=3, max_length=50)] = None
    is_active: bool | None = None
    parent_id: int | None = None


class CategoryPublic(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: Annotated[str, Field(min_length=3, max_length=50)]
    parent_id: int | None


class CategoryPrivate(CategoryPublic):
    is_active: bool


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
    rating: Mapped[float] = mapped_column(
        Numeric(asdecimal=False), default=0.0, nullable=False
    )
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=False, index=True
    )
    seller_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )

    category: Mapped[Category] = relationship(back_populates="products")
    seller: Mapped[User] = relationship(back_populates="products")
    reviews: Mapped[list[Review]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )


class ProductBase(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=100)]
    description: Annotated[str | None, Field(max_length=500)] = None
    price: Annotated[Decimal, Field(gt=Decimal("0"), decimal_places=2)]
    image_url: Annotated[str | None, Field(max_length=200)] = None
    stock: Annotated[int, Field(ge=0)]
    category_id: int


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Annotated[str | None, Field(max_length=100)] = None
    description: Annotated[str | None, Field(max_length=500)] = None
    price: Annotated[Decimal | None, Field(gt=Decimal(0), decimal_places=2)] = None
    image_url: Annotated[str | None, Field(max_length=200)] = None
    stock: Annotated[int | None, Field(ge=0)] = None
    is_active: bool | None = None
    category_id: int | None = None


class ProductPublic(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rating: float
    seller_id: int


class ProductPrivate(ProductPublic):
    is_active: bool


class ProductPublicWithCategory(ProductPublic):
    category: CategoryPublic


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    grade: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=partial(datetime.now, tz=UTC), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False, index=True
    )
    reviewer: Mapped[User] = relationship(back_populates="reviews")
    product: Mapped[Product] = relationship(back_populates="reviews")


class ReviewBase(BaseModel):
    comment: Annotated[str | None, Field(max_length=500)] = None
    grade: Annotated[int, Field(ge=1, le=5)]
    product_id: int


class ReviewCreate(ReviewBase):
    pass


class ReviewUpdate(BaseModel):
    comment: Annotated[str | None, Field(max_length=500)] = None
    grade: Annotated[int | None, Field(ge=1, le=5)] = None
    product_id: int | None = None
    is_active: bool | None = None


class ReviewPublic(ReviewBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    user_id: int


class ReviewPrivate(ReviewPublic):
    is_active: bool
