from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.deps import CurrenActivetAdminDep, SessionDep
from app.models import (
    Category,
    CategoryCreate,
    CategoryPrivate,
    CategoryPublic,
    CategoryUpdate,
    Product,
    ProductPublic,
)

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post(
    "/",
    tags=["admin"],
    status_code=status.HTTP_201_CREATED,
    response_model=CategoryPrivate,
)
async def create_category(
    *, session: SessionDep, _admin: CurrenActivetAdminDep, category: CategoryCreate
) -> Category:
    # Our new category can be a child of another.
    # If so, ensure the partent category exists and is currently active.
    if category.parent_id is not None:
        result = await session.execute(
            select(Category).where(
                Category.id == category.parent_id, Category.is_active
            )
        )
        parent_category = result.scalars().first()
        if not parent_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Parent category '{category.parent_id}' not found or inactive"
                ),
            )

    db_category = Category(**category.model_dump())

    session.add(db_category)

    await session.commit()
    await session.refresh(db_category)

    return db_category


@router.get("/", response_model=list[CategoryPublic])
async def read_categories(
    *,
    session: SessionDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(gt=0)] = 100,
) -> Sequence[Category]:
    # Fetch top-level and nested categories that are currently active.
    # Using offset-based pagination to handle large lists.
    result = await session.execute(
        select(Category).where(Category.is_active).offset(offset).limit(limit)
    )
    categories = result.scalars().all()

    return categories


@router.get("/{category_id}/products", response_model=list[ProductPublic])
async def read_category_products(
    *,
    session: SessionDep,
    category_id: int,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(gt=0)] = 100,
) -> Sequence[Product]:
    result = await session.execute(
        select(Product)
        .join(Product.category)
        .where(
            Product.category_id == category_id,
            Category.is_active,
            Product.is_active,
        )
        .offset(offset)
        .limit(limit)
    )
    products = result.scalars().all()
    # Handle empty list as well as product's category not found or inactive.
    if not products:
        result = await session.execute(
            select(Category.id).where(Category.id == category_id, Category.is_active)
        )
        category = result.scalars().first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=rf"Category '{category_id}' not found or inactive",
            )

    return products


@router.patch("/{category_id}", tags=["admin"], response_model=CategoryPrivate)
async def update_category(
    *,
    session: SessionDep,
    _admin: CurrenActivetAdminDep,
    category_id: int,
    category: CategoryUpdate,
) -> Category:
    # Ensure the category exists.
    result = await session.execute(select(Category).where(Category.id == category_id))
    db_category = result.scalars().first()
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category '{category_id}' not found",
        )

    # Our updated category can be a child of another.
    # If so, ensure the partent category exists and is currently active.
    if category.parent_id is not None:
        result = await session.execute(
            select(Category).where(
                Category.id == category.parent_id, Category.is_active
            )
        )
        parent_category = result.scalars().first()
        if not parent_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Parent category '{category.parent_id}' not found or inactive"
                ),
            )

    # Update the category, make sure to remove unset fields.
    update_data = category.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)

    await session.commit()
    await session.refresh(db_category)

    return db_category
