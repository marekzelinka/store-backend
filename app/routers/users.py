from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.core.security import hash_password
from app.deps import CurrentActiveUserDep, SessionDep
from app.models import User, UserCreate, UserPrivate, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=UserPrivate,
)
async def create_user(*, session: SessionDep, user: UserCreate) -> User:
    result = await session.execute(
        select(User).where(func.lower(User.username) == user.username.lower())
    )
    duplicate_username_user = result.scalars().first()
    if duplicate_username_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists"
        )

    result = await session.execute(
        select(User).where(func.lower(User.email) == user.email.lower())
    )
    duplicate_email_user = result.scalars().first()
    if duplicate_email_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists"
        )

    db_user = User(
        **user.model_dump(exclude={"email", "password"}),
        email=user.email.lower(),
        password_hash=hash_password(user.password),
    )

    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)

    return db_user


@router.get("/me", response_model=UserPrivate)
async def read_current_user(*, user: CurrentActiveUserDep) -> User:
    return user


@router.patch("/me", response_model=UserPrivate)
async def update_current_user(
    *, session: SessionDep, user: CurrentActiveUserDep, updates: UserUpdate
) -> User:
    if updates.username is not None:
        result = await session.execute(
            select(User).where(func.lower(User.username) == user.username.lower())
        )
        duplicate_username_user = result.scalars().first()
        if duplicate_username_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

        user.username = updates.username

    if updates.email is not None:
        result = await session.execute(
            select(User).where(func.lower(User.email) == user.email.lower())
        )
        duplicate_email_user = result.scalars().first()
        if duplicate_email_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists"
            )

        user.email = updates.email.lower()

    if updates.password is not None:
        user.password_hash = hash_password(updates.password)

    await session.commit()
    await session.refresh(user)

    return user
