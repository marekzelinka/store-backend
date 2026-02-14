from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.core.config import config
from app.core.security import hash_password
from app.deps import CurrentActiveUserDep, SessionDep
from app.models import (
    User,
    UserCreate,
    UserPrivate,
    UserRole,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "",
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
async def read_current_user(*, current_active_user: CurrentActiveUserDep) -> User:
    return current_active_user


@router.patch("/me", response_model=UserPrivate)
async def update_current_user(
    *, session: SessionDep, current_user: CurrentActiveUserDep, user: UserUpdate
) -> User:
    # First admin is special and cannot be updated.
    if (
        current_user.role == UserRole.admin
        and current_user.username == config.first_admin
    ):
        return current_user

    if user.username is not None:
        result = await session.execute(
            select(User).where(func.lower(User.username) == user.username.lower())
        )
        duplicate_username_user = result.scalars().first()
        if duplicate_username_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

        current_user.username = user.username

    if user.email is not None:
        result = await session.execute(
            select(User).where(func.lower(User.email) == current_user.email.lower())
        )
        duplicate_email_user = result.scalars().first()
        if duplicate_email_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists"
            )

        current_user.email = user.email.lower()

    if user.password is not None:
        current_user.password_hash = hash_password(user.password)

    await session.commit()
    await session.refresh(current_user)

    return current_user
