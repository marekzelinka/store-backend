from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    role: str = Field(default="buyer", pattern="^(buyer|seller|admin)$")


class UserCreate(UserBase):
    email: EmailStr = Field(max_length=120)
    password: str = Field(min_length=8)


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=50)
    email: EmailStr | None = Field(default=None, max_length=120)
    is_active: bool | None = None
    role: str | None = Field(default=None, pattern="^(buyer|seller|admin)$")


class UserPublic(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class UserPrivate(UserPublic):
    email: EmailStr = Field(max_length=120)
    is_active: bool


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    parent_id: int | None = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    is_active: bool | None = None
    parent_id: int | None = None


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
    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    price: Decimal | None = Field(
        default=None, gt=Decimal(0), decimal_places=3, max_digits=5
    )
    image_url: str | None = Field(default=None, max_length=200)
    stock: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    category_id: int | None = None


class ProductPublic(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool


class ProductPublicWithCategory(ProductPublic):
    category: CategoryPublic
