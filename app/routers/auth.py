from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import delete, func, select
from sqlalchemy.orm import joinedload

from app.core.config import config
from app.core.security import (
    create_access_token,
    generate_secure_token,
    verify_password,
)
from app.deps import CurrentActiveUserDep, SessionDep
from app.models import RefreshToken, RefreshTokenRequest, Token, User

router = APIRouter(tags=["auth"])


@router.post("/token")
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
            detail="Incorrect email or password or user is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token with user id as subject
    access_token_expires = timedelta(minutes=config.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires,
    )

    # Create refresh token
    refresh_token_expires = timedelta(minutes=config.refresh_token_expire_minutes)
    refresh_token = generate_secure_token()

    session.add(
        RefreshToken(
            token=refresh_token,
            user_id=user.id,
            expired_at=datetime.now(tz=UTC) + refresh_token_expires,
        )
    )

    await session.commit()

    return Token(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


@router.post("/refresh")
async def refresh_access_token(
    *, session: SessionDep, _user: CurrentActiveUserDep, data: RefreshTokenRequest
) -> Token:
    result = await session.execute(
        select(RefreshToken)
        .options(joinedload(RefreshToken.user))
        .where(RefreshToken.token == data.refresh_token)
    )
    refresh_token = result.scalars().first()
    if not refresh_token or refresh_token.expired_at < datetime.now(tz=UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = refresh_token.user
    if not user.is_active:
        await session.delete(refresh_token)

        await session.commit()

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is disabled",
        )

    # Rotation: Delete used token
    await session.delete(refresh_token)

    # Clean up other expired tokens for this specific user
    await session.execute(
        delete(RefreshToken).where(
            RefreshToken.user_id == user.id,
            RefreshToken.expired_at < datetime.now(tz=UTC),
        )
    )

    # Create new pair
    new_refresh_token_expires = timedelta(minutes=config.refresh_token_expire_minutes)
    new_refresh_token = generate_secure_token()
    session.add(
        RefreshToken(
            token=new_refresh_token,
            user_id=user.id,
            expired_at=datetime.now(tz=UTC) + new_refresh_token_expires,
        )
    )

    access_token_expires = timedelta(minutes=config.access_token_expire_minutes)
    new_access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires,
    )

    await session.commit()

    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    *, session: SessionDep, _user: CurrentActiveUserDep, data: RefreshTokenRequest
) -> None:
    """
    Revokes a session by deleting the refresh token from the database.
    """
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.token == data.refresh_token)
    )
    refresh_token = result.scalars().first()
    if refresh_token:
        await session.delete(refresh_token)

        await session.commit()
