from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    name: Annotated[str, Field(min_length=3, max_length=50)]


class CategoryPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class ProductCreate(BaseModel):
    name: Annotated[str, Field(min_length=3, max_length=100)]
    description: Annotated[str | None, Field(max_length=500)] = None
    price: Annotated[Decimal, Field(gt=Decimal(0))]
    stock: Annotated[int, Field(ge=0)]

    category_id: int


class ProductPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    price: Annotated[Decimal, Field(gt=Decimal(0), decimal_places=2)]
    stock: int
    is_active: bool

    category_id: int
