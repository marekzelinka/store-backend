from collections.abc import Sequence

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.deps import SessionDep
from app.models import Category, Product
from app.schemas import ProductCreate, ProductPublicWithCategory, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])


@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=ProductPublicWithCategory
)
async def create_product(*, session: SessionDep, product: ProductCreate) -> Product:
    result = await session.execute(
        select(Category).where(Category.id == product.category_id, Category.is_active)
    )
    db_category = result.scalars().first()
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=rf"Category {product.category_id} not found or is inactive",
        )

    db_product = Product(**product.model_dump())

    session.add(db_product)
    await session.commit()
    await session.refresh(db_product, attribute_names=["category"])

    return db_product


@router.get("/", response_model=list[ProductPublicWithCategory])
async def read_products(*, session: SessionDep) -> Sequence[Product]:
    result = await session.execute(
        select(Product)
        .options(selectinload(Product.category))
        .where(Product.is_active, Category.is_active)
    )

    return result.scalars().all()


@router.get("/{product_id}", response_model=ProductPublicWithCategory)
async def read_product(*, session: SessionDep, product_id: int) -> Product:
    result = await session.execute(
        select(Product)
        .options(selectinload(Product.category))
        .where(Product.id == product_id, Product.is_active, Category.is_active)
    )
    db_product = result.scalars().first()
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=rf"Category {product_id} not found or is inactive",
        )

    return db_product


@router.patch("/{product_id}", response_model=ProductPublicWithCategory)
async def update_product(
    *, session: SessionDep, product_id: int, product: ProductUpdate
) -> Product:
    result = await session.execute(select(Product).where(Product.id == product_id))
    db_product = result.scalars().first()
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    product_data = product.model_dump(exclude_unset=True)
    for field, value in product_data.items():
        setattr(db_product, field, value)

    await session.commit()
    await session.refresh(db_product, attribute_names=["category"])

    return db_product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(*, session: SessionDep, product_id: int) -> None:
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=rf"Product {product_id} not found",
        )

    await session.delete(product)
    await session.commit()
