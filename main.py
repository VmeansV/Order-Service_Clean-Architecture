from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.presentation.api import router
from app.presentation.dependencies import catalog_client, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await catalog_client.close()
    await engine.dispose()


app = FastAPI(title="Order Service", lifespan=lifespan)
app.include_router(router)
