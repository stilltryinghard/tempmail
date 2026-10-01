import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.emails.router import router as email_router
from app.messages.router import router as messages_router
from app.messages.router import webhook_router
from app.cleanup import cleanup_loop
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(cleanup_loop())
    yield
    task.cancel()


app = FastAPI(title="Tempmail Service", lifespan=lifespan)

# Подключение роутера ящиков.
app.include_router(email_router)
app.include_router(messages_router)
app.include_router(webhook_router)


@app.get("/health")
def health_check():
    return {"status": "alive"}
