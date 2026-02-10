from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None


class CategoryPublic(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int

    is_active: bool


class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    price: Decimal = Field(gt=Decimal(0), decimal_places=3, max_digits=5)
    image_url: str | None = Field(default=None, max_length=200)
    stock: int = Field(ge=0)

    category_id: int


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: Decimal | None = None
    image_url: str | None = None
    stock: int | None = None
    is_active: bool | None = None

    category_id: int | None = None


class ProductPublic(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool


class ProductPublicWithCategory(ProductPublic):
    category: CategoryPublic


class Message(BaseModel):
    message: str
