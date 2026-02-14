from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import func, select

from app.core.config import config
from app.core.db import SessionLocal
from app.core.security import hash_password
from app.models import User, UserRole
from app.routers import auth, categories, products, reviews, users


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    async with SessionLocal() as session:
        result = await session.execute(
            select(User).where(func.lower(User.username) == config.first_admin.lower())
        )
        admin = result.scalars().first()
        if not admin:
            session.add(
                User(
                    username=config.first_admin,
                    email=config.first_admin_email.lower(),
                    password_hash=hash_password(
                        config.first_admin_password.get_secret_value()
                    ),
                    role=UserRole.admin,
                )
            )

            await session.commit()

    yield


app = FastAPI(title="E-Commerce API", version="1.0.0", lifespan=lifespan)

# Set all CORS enabled origins
if config.all_cors_origins:
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,  # ty:ignore[invalid-argument-type]
        allow_origins=config.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(reviews.router)
