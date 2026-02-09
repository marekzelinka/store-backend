from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.db import engine
from app.models import Base
from app.routers import categories, products


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    # Create database on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Cleanup on shutdown
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.include_router(categories.router)
app.include_router(products.router)
