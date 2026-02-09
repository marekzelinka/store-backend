from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.deps import SessionDep
from app.models import Category, Product
from app.schemas import ProductCreate, ProductPublic

router = APIRouter(prefix='/products', tags=['products'])


@router.post('', status_code=status.HTTP_201_CREATED, response_model=ProductPublic)
async def create_product(*, session: SessionDep, product: ProductCreate) -> Product:
    result = await session.execute(
        select(Category).where(Category.id == product.category_id, Category.is_active)
    )
    db_category = result.scalars().first()
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=rf'Category {product.category_id} not found or is inactive',
        )

    db_product = Product(**product.model_dump())

    session.add(db_product)
    await session.commit()
    await session.refresh(db_product)

    return db_product
