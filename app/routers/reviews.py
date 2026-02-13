from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.deps import CurrentActiveBuyerDep, CurrentActiveUserDep, SessionDep
from app.models import (
    Product,
    Review,
    ReviewCreate,
    ReviewPrivate,
    ReviewPublic,
    ReviewUpdate,
    UserRole,
)

router = APIRouter(prefix="/reviews", tags=["reviews"])


async def update_product_rating(*, session: AsyncSession, product_id: int) -> None:
    """
    Updates the average rating for product based on each review grade.
    Ensuring the updated product and reviews are both currently active.
    """
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
    # Verify if the product existed/rating was updated.
    if not updated_product_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product '{product_id}' not found or inactive",
        )

    await session.commit()


@router.post(
    "/",
    tags=["buyer"],
    status_code=status.HTTP_201_CREATED,
    response_model=ReviewPublic,
)
async def create_review(
    *, session: SessionDep, buyer: CurrentActiveBuyerDep, review: ReviewCreate
) -> Review:
    # Ensure the product exists and currently active.
    result = await session.execute(
        select(Product).where(Product.id == review.product_id, Product.is_active)
    )
    product = result.scalars().first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product '{review.product_id}' not found or inactive",
        )

    # Ensure that the buyer can only leave one review for a product.
    result = await session.execute(
        select(Review).where(
            Review.user_id == buyer.id,
            Review.product_id == product.id,
            Review.is_active,
        )
    )
    existing_review = result.scalars().first()
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Users can post only one review for the product",
        )

    db_review = Review(**review.model_dump(), user_id=buyer.id)

    session.add(db_review)

    await session.commit()
    await session.refresh(db_review)

    # Re-calculate the average rating for a given product.
    # Ensure the new review was saved to the database, so that the it's grade is
    # included in the average rating.
    await update_product_rating(session=session, product_id=review.product_id)

    return db_review


@router.patch("/{review_id}", tags=["admin", "buyer"], response_model=ReviewPrivate)
async def update_review(
    *,
    session: SessionDep,
    user: CurrentActiveUserDep,
    review_id: int,
    review: ReviewUpdate,
) -> Review:
    if user.role not in (UserRole.admin, UserRole.buyer):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only buyers and admins can perform this action",
        )

    # Ensure the review exists.
    result = await session.execute(select(Review).where(Review.id == review_id))
    db_review = result.scalars().first()
    if not db_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review {str(review_id)!r} not found",
        )
    # Check if user is buyer, if so make sure review belongs to them.
    if user.role == UserRole.buyer and user.id != db_review.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Users can only delete their own reviews",
        )

    # Update data can include a new product.
    # If so, ensure the product exists and is currently active.
    if review.product_id is not None:
        result = await session.execute(
            select(Product).where(Product.id == review.product_id, Product.is_active)
        )
        product = result.scalars().first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(rf"Product '{review.product_id}' not found or is inactive"),
            )

    # Update the review, make sure to remove unset fields.
    update_data = review.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_review, field, value)

    await session.commit()
    await session.refresh(db_review)

    # Re-calculate the average rating for a given product.
    # The review could have been deactivated or the product it belongs to could have
    # been changed.
    # Ensure the updated review was saved to the database, so that the it's grade is
    # included in the average rating.
    await update_product_rating(session=session, product_id=db_review.product_id)

    return db_review
