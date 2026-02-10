from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.deps import CurrentAdminDep, SessionDep
from app.models import Category
from app.schemas import CategoryCreate, CategoryPublic, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=CategoryPublic)
async def create_category(
    *, session: SessionDep, _current_admin: CurrentAdminDep, category: CategoryCreate
) -> Category:
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
                    f"Parent category {str(category.parent_id)!r} not found or inactive"
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
    result = await session.execute(
        select(Category).where(Category.is_active).offset(offset).limit(limit)
    )
    categories = result.scalars().all()

    return categories


@router.patch("/{category_id}", response_model=CategoryPublic)
async def update_category(
    *,
    session: SessionDep,
    _current_admin: CurrentAdminDep,
    category_id: int,
    category: CategoryUpdate,
) -> Category:
    result = await session.execute(
        select(Category).where(Category.id == category_id, Category.is_active)
    )
    db_category = result.scalars().first()
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category {str(category_id)!r} not found or inactive",
        )

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
                    f"Parent category {str(category.parent_id)!r} not found or inactive"
                ),
            )

    category_data = category.model_dump(exclude_unset=True)
    for field, value in category_data.items():
        setattr(db_category, field, value)

    await session.commit()
    await session.refresh(db_category)

    return db_category


@router.patch(
    "/{category_id}/deactivate",
    response_model=CategoryPublic,
)
async def mark_category_as_inactive(
    *, session: SessionDep, _current_admin: CurrentAdminDep, category_id: int
) -> Category:
    result = await session.execute(select(Category).where(Category.id == category_id))
    category = result.scalars().first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=rf"Category {str(category_id)!r} not found",
        )

    category.is_active = False

    await session.commit()
    await session.refresh(category)

    return category
