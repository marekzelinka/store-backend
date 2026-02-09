from decimal import Decimal

from sqlalchemy import Boolean, Integer, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Category(Base):
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(length=50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Product(Base):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(length=100))
    description: Mapped[str | None] = mapped_column(String(length=500), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2))
    stock: Mapped[int] = mapped_column(Integer())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
