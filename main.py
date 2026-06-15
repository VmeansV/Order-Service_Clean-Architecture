from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI

from app.config import settings
from app.presentation.api import router
from app.presentation.dependencies import catalog_client, engine, payments_client

if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=1.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await catalog_client.close()
    await payments_client.close()
    await engine.dispose()


app = FastAPI(title="Order Service", lifespan=lifespan)
app.include_router(router)
