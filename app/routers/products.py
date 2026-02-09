from fastapi import APIRouter, status

from app.deps import SessionDep
from app.models import Product
from app.schemas import ProductCreate

router = APIRouter(prefix='/products', tags=['products'])


@router.post('', status_code=status.HTTP_201_CREATED)
async def create_product(*, session: SessionDep, product: ProductCreate) -> Product:
    db_product = Product(**product.model_dump())

    session.add(db_product)
    await session.commit()
    await session.refresh(db_product)

    return db_product
