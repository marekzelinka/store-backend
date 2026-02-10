from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select

from app.core.config import config
from app.core.security import create_access_token, hash_password, verify_password
from app.deps import CurrentActiveUserDep, SessionDep
from app.models import User
from app.schemas import Token, UserCreate, UserPrivate

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


@router.post("/token", tags=["auth"])
async def login_for_access_token(
    *,
    session: SessionDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    # Look up user by email (case-insensitive)
    # Note: OAuth2PasswordRequestForm uses "username" field, but we treat it as email
    result = await session.execute(
        select(User).where(
            func.lower(User.email) == form_data.username.lower(), User.is_active
        ),
    )
    user = result.scalars().first()

    # Verify user exists and password is correct
    # Don't reveal which one failed (security best practice)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token with user id as subject
    access_token_expires = timedelta(minutes=config.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", tags=["auth"], response_model=UserPrivate)
async def read_current_user(*, current_user: CurrentActiveUserDep) -> User:
    return current_user
