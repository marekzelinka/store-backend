from fastapi import APIRouter, status

from app.deps import SessionDep
from app.models import Category
from app.schemas import CategoryCreate, CategoryPublic

router = APIRouter(prefix='/categories', tags=['categories'])


@router.post('', status_code=status.HTTP_201_CREATED, response_model=CategoryPublic)
async def create_category(*, session: SessionDep, category: CategoryCreate) -> Category:
    db_category = Category(**category.model_dump())

    session.add(db_category)
    await session.commit()
    await session.refresh(db_category)

    return db_category
