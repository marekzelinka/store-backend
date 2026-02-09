from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    name: Annotated[str, Field(min_length=3, max_length=50)]


class CategoryUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None


class CategoryPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    is_active: bool


class ProductCreate(BaseModel):
    name: Annotated[str, Field(min_length=3, max_length=100)]
    description: Annotated[str | None, Field(max_length=500)] = None
    price: Annotated[Decimal, Field(gt=Decimal(0))]
    stock: Annotated[int, Field(ge=0)]

    category_id: int


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: Decimal | None = None
    stock: int | None = None
    is_active: bool | None = None

    category_id: int | None = None


class ProductPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    price: Annotated[Decimal, Field(gt=Decimal(0), decimal_places=2)]
    stock: int
    is_active: bool

    category_id: int


class ProductPublicWithCategory(ProductPublic):
    category: CategoryPublic
