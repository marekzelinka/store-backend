from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.deps import SessionDep
from app.models import Category
from app.schemas import CategoryCreate, CategoryPublic, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=CategoryPublic)
async def create_category(*, session: SessionDep, category: CategoryCreate) -> Category:
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
    active: bool | None = None,
) -> Sequence[Category]:
    query = select(Category)
    if active is not None:
        query = query.where(Category.is_active == active)

    result = await session.execute(query.offset(offset).limit(limit))
    categories = result.scalars().all()

    return categories


@router.patch("/{category_id}", response_model=CategoryPublic)
async def update_category(
    *, session: SessionDep, category_id: int, category: CategoryUpdate
) -> Category:
    result = await session.execute(select(Category).where(Category.id == category_id))
    db_category = result.scalars().first()
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category {category_id} not found",
        )

    category_data = category.model_dump(exclude_unset=True)
    for field, value in category_data.items():
        setattr(db_category, field, value)

    await session.commit()
    await session.refresh(db_category)

    return db_category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(*, session: SessionDep, category_id: int) -> None:
    result = await session.execute(select(Category).where(Category.id == category_id))
    db_category = result.scalars().first()
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=rf"Category {category_id} not found",
        )

    await session.delete(db_category)
    await session.commit()
