import pytest_asyncio
import pytest
from pydantic import SecretStr
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.redis_client import redis_client

TEST_BREVO_TOKEN = "test-brevo-token"


TEST_DATABASE_URL = (
    f"postgresql+asyncpg://"
    f"{settings.postgres_user}:{settings.postgres_password.get_secret_value()}"
    f"@{settings.postgres_host}:{settings.postgres_port}"
    f"/tempmail_test"
)


@pytest_asyncio.fixture(autouse=True)
async def clear_redis():
    await redis_client.flushdb()
    yield


# движок — ОДИН на всю сессию, в session-loop
@pytest_asyncio.fixture(scope="session")
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL)
    yield engine
    await engine.dispose()


# таблицы — пересоздаются на КАЖДЫЙ тест (изоляция), но движок тот же
@pytest_asyncio.fixture(autouse=True)
async def setup_db(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(engine):
    session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def brevo_token(monkeypatch):
    monkeypatch.setattr(settings, "brevo_webhook_secret", SecretStr(TEST_BREVO_TOKEN))


@pytest.fixture
def brevo_headers():
    return {"Authorization": f"Bearer {TEST_BREVO_TOKEN}"}
