from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from app.deps import CurrentActiveSellerDep, CurrentActiveUserDep, SessionDep
from app.models import (
    Category,
    Product,
    ProductCreate,
    ProductPrivate,
    ProductPublicWithCategory,
    ProductUpdate,
    Review,
    ReviewPublic,
    UserRole,
)

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ProductPrivate)
async def create_product(
    *,
    session: SessionDep,
    seller: CurrentActiveSellerDep,
    product: ProductCreate,
) -> Product:
    # Ensure the assigned category exists and currently active.
    result = await session.execute(
        select(Category).where(Category.id == product.category_id, Category.is_active)
    )
    category = result.scalars().first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=rf"Category '{product.category_id}' not found or inactive",
        )

    db_product = Product(**product.model_dump(), seller_id=seller.id)

    session.add(db_product)

    await session.commit()
    await session.refresh(db_product)

    return db_product


@router.get("/", response_model=list[ProductPublicWithCategory])
async def read_products(
    *,
    session: SessionDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(gt=0)] = 100,
) -> Sequence[Product]:
    # Fetch products and assigned categories.
    # Ensue both the product and category are currently active.
    # Using offset-based pagination to handle large lists.
    result = await session.execute(
        select(Product)
        .options(selectinload(Product.category))
        .where(Product.is_active, Category.is_active)
        .offset(offset)
        .limit(limit)
    )
    products = result.scalars().all()

    return products


@router.get("/{product_id}", response_model=ProductPublicWithCategory)
async def read_product(*, session: SessionDep, product_id: int) -> Product:
    # Ensure the product exists and currently active.
    # Also ensure taht the product category exists and currently active.
    result = await session.execute(
        select(Product)
        .options(joinedload(Product.category))
        .join(Product.category)
        .where(Product.id == product_id, Product.is_active, Category.is_active)
    )
    product = result.scalars().first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=rf"Product '{product_id}' not found or belongs to inactive category",
        )

    return product


@router.get("/{product_id}/reviews", response_model=list[ReviewPublic])
async def read_product_reviews(
    *,
    session: SessionDep,
    product_id: int,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(gt=0)] = 100,
) -> Sequence[Review]:
    # Fetch reviews that belong to this product
    result = await session.execute(
        select(Review)
        .join(Review.product)
        .where(
            Review.product_id == product_id,
            Product.is_active,
            Review.is_active,
        )
        .offset(offset)
        .limit(limit)
    )
    reviews = result.scalars().all()
    # Handle empty list as well as product not found or inactive
    if not reviews:
        result = await session.execute(
            select(Product.id).where(Product.id == product_id, Product.is_active)
        )
        product = result.scalars().first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=rf"Product '{product_id}' not found or inactive",
            )

    return reviews


@router.patch("/{product_id}", response_model=ProductPrivate)
async def update_product(
    *,
    session: SessionDep,
    user: CurrentActiveUserDep,
    product_id: int,
    product: ProductUpdate,
) -> Product:
    if user.role not in (UserRole.admin, UserRole.seller):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only sellers and admins can perform this action",
        )

    # Ensure the product exists.
    result = await session.execute(select(Product).where(Product.id == product_id))
    db_product = result.scalars().first()
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=rf"Product '{product_id}' not found",
        )
    # Check if user is seller, if so make sure product belongs to them.
    if user.role == UserRole.seller and user.id != db_product.seller_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=r"You can only update your own products",
        )

    # Update data can include a new category.
    # If so, ensure the category exists and is currently active.
    if product.category_id is not None:
        result = await session.execute(
            select(Category).where(
                Category.id == product.category_id, Category.is_active
            )
        )
        category = result.scalars().first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(rf"Category '{product.category_id}' not found or is inactive"),
            )

    # Update the product,, make sure to remove unset fields.
    update_data = product.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)

    await session.commit()
    await session.refresh(db_product)

    return db_product
