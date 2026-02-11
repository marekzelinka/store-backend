from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.deps import CurrentSellerDep, SessionDep
from app.models import Category, Product
from app.schemas import (
    ProductCreate,
    ProductPublic,
    ProductPublicWithCategory,
    ProductUpdate,
)

router = APIRouter(prefix="/products", tags=["products"])


@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=ProductPublicWithCategory
)
async def create_product(
    *, session: SessionDep, current_seller: CurrentSellerDep, product: ProductCreate
) -> Product:
    result = await session.execute(
        select(Category).where(Category.id == product.category_id, Category.is_active)
    )
    category = result.scalars().first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=rf"Category {str(product.category_id)!r} not found or inactive",
        )

    db_product = Product(**product.model_dump(), seller_id=current_seller.id)
    session.add(db_product)

    await session.commit()
    await session.refresh(db_product, attribute_names=["category"])

    return db_product


@router.get("/", response_model=list[ProductPublicWithCategory])
async def read_products(
    *,
    session: SessionDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(gt=0)] = 100,
) -> Sequence[Product]:
    query = (
        select(Product)
        .options(selectinload(Product.category))
        .where(Product.is_active, Category.is_active)
    )
    result = await session.execute(query.offset(offset).limit(limit))
    products = result.scalars().all()

    return products


@router.get("/categories/{category_id}", response_model=list[ProductPublic])
async def read_products_by_category(
    *,
    session: SessionDep,
    category_id: int,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(gt=0)] = 100,
) -> Sequence[Product]:
    result = await session.execute(
        select(Category).where(Category.id == category_id, Category.is_active)
    )
    category = result.scalars().first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=rf"Category {str(category_id)!r} not found or inactive",
        )

    result = await session.execute(
        select(Product)
        .where(Product.category_id == category_id, Product.is_active)
        .offset(offset)
        .limit(limit)
    )
    products = result.scalars().all()

    return products


@router.get("/{product_id}", response_model=ProductPublicWithCategory)
async def read_product(*, session: SessionDep, product_id: int) -> Product:
    result = await session.execute(
        select(Product)
        .options(selectinload(Product.category))
        .where(Product.id == product_id, Product.is_active)
    )
    product = result.scalars().first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=rf"Category {str(product_id)!r} not found or inactive",
        )

    result = await session.execute(
        select(Category).where(Category.id == product.category_id, Category.is_active)
    )
    category = result.scalars().first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                rf"Product category {str(product.category_id)!r} not found or inactive"
            ),
        )

    return product


@router.patch("/{product_id}", response_model=ProductPublicWithCategory)
async def update_product(
    *,
    session: SessionDep,
    current_seller: CurrentSellerDep,
    product_id: int,
    product: ProductUpdate,
) -> Product:
    result = await session.execute(
        select(Product).where(Product.id == product_id, Product.is_active)
    )
    db_product = result.scalars().first()
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=rf"Product {str(product_id)!r} not found or inactive",
        )
    if db_product.seller_id != current_seller.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=r"You can only update your own products",
        )

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
                detail=(
                    rf"Category {str(product.category_id)!r} not found or is inactive"
                ),
            )

    product_data = product.model_dump(exclude_unset=True)
    for field, value in product_data.items():
        setattr(db_product, field, value)

    await session.commit()
    await session.refresh(db_product, attribute_names=["category"])

    return db_product


@router.patch("/{product_id}/deactivate", response_model=ProductPublic)
async def mark_product_as_inactive(
    *, session: SessionDep, current_seller: CurrentSellerDep, product_id: int
) -> Product:
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=rf"Product {product_id} not found",
        )
    if product.seller_id != current_seller.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=r"You can only deactivate your own products",
        )

    product.is_active = False

    await session.commit()
    await session.refresh(product)

    return product
