from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import SessionLocal
from app.core.security import oauth2_scheme, verify_access_token
from app.models import User, UserRole

TokenDep = Annotated[str, Depends(oauth2_scheme)]


async def get_session() -> AsyncGenerator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid authentication credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(session: SessionDep, token: TokenDep) -> User:
    user_id = verify_access_token(token)
    if user_id is None:
        raise credentials_exception

    # Validate user_id is a valid integer
    try:
        user_id = int(user_id)
    except (TypeError, ValueError) as err:
        raise credentials_exception from err

    results = await session.execute(select(User).where(User.id == user_id))
    user = results.scalars().first()
    if not user:
        raise credentials_exception

    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


async def get_current_active_user(current_user: CurrentUserDep) -> User:
    if not current_user.is_active:
        raise credentials_exception

    return current_user


CurrentActiveUserDep = Annotated[User, Depends(get_current_active_user)]


async def get_current_seller(current_user: CurrentActiveUserDep) -> User:
    if current_user.role != UserRole.seller:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only sellers can perform this action",
        )

    return current_user


CurrentActiveSellerDep = Annotated[User, Depends(get_current_seller)]


async def get_current_buyer(current_user: CurrentActiveUserDep) -> User:
    if current_user.role != UserRole.buyer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only buyers can perform this action",
        )

    return current_user


CurrentActiveBuyerDep = Annotated[User, Depends(get_current_buyer)]


async def get_current_admin(current_user: CurrentActiveUserDep) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can perform this action",
        )

    return current_user


CurrenActivetAdminDep = Annotated[User, Depends(get_current_admin)]
