from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import config

engine = create_async_engine(
    str(config.sqlalchemy_database_url),
    connect_args={'check_same_thread': False},
    echo=True,
)
SessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)
