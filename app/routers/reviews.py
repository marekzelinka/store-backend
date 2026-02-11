from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.deps import CurrentBuyerDep, SessionDep
from app.models import Product, Review
from app.schemas import ReviewCreate, ReviewPublic

router = APIRouter(prefix="/reviews", tags=["reviews"])


async def update_product_rating(*, session: AsyncSession, product_id: int) -> None:
    avg_query = (
        select(func.avg(Review.grade))
        .where(Review.product_id == product_id, Review.is_active)
        .scalar_subquery()
    )

    update_query = (
        update(Product)
        .where(Product.id == product_id, Product.is_active)
        .values(rating=avg_query)
        .returning(Product.id)
    )

    result = await session.execute(update_query)
    updated_product_id = result.scalars().first()
    # Verify if the product existed/rating was updated
    if not updated_product_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product {str(product_id)!r} not found or inactive",
        )

    await session.commit()


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ReviewPublic)
async def create_review(
    *, session: SessionDep, current_buyer: CurrentBuyerDep, review: ReviewCreate
) -> Review:
    result = await session.execute(
        select(Product).where(Product.id == review.product_id, Product.is_active)
    )
    product = result.scalars().first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product {str(review.product_id)!r} not found or inactive",
        )

    db_review = Review(**review.model_dump(), user_id=current_buyer.id)
    session.add(db_review)

    await session.commit()
    await session.refresh(db_review)

    await update_product_rating(session=session, product_id=review.product_id)

    return db_review


@router.get("/", response_model=list[ReviewPublic])
async def read_reviews(
    *,
    session: SessionDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(gt=0)] = 100,
) -> Sequence[Review]:
    result = await session.execute(
        select(Review).where(Review.is_active).offset(offset).limit(limit)
    )
    reviews = result.scalars().all()

    return reviews
