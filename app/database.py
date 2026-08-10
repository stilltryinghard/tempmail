from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession
)
from sqlalchemy.orm import DeclarativeBase
from collections.abc import AsyncGenerator

from app.config import settings

#Декларативная база - от нее наследуются все модели
class Base(DeclarativeBase):
    pass

# Собираем строку подключения из конфига
DATABASE_URL = (
    f"postgresql+asyncpg://"
    f"{settings.postgres_user}:{settings.postgres_password.get_secret_value()}"
    f"@{settings.postgres_host}:{settings.postgres_port}"
    f"/{settings.postgres_db}"
)

#Engine - один на приложение, держит пул соединений
engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True,
    echo=settings.debug,
)

#Фабрика сессий
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

#Dependency для FastAPI - выдает сессию на запрос, потом закрывает
#контекстный менеджер сам закроет сессию после запроса
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
        