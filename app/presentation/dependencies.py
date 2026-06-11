from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.application.create_order import CreateOrderUseCase
from app.config import settings
from app.infrastructure.http_clients import CatalogServiceClient
from app.infrastructure.unit_of_work import UnitOfWork

engine = create_async_engine(settings.async_database_url)
session_factory = async_sessionmaker(engine, expire_on_commit=False)

catalog_client = CatalogServiceClient(
    base_url=settings.capashino_base_url, api_key=settings.lms_api_key
)


def get_unit_of_work() -> UnitOfWork:
    return UnitOfWork(session_factory)


def get_catalog_client() -> CatalogServiceClient:
    return catalog_client


def get_create_order_use_case(
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
    catalog_client: Annotated[CatalogServiceClient, Depends(get_catalog_client)],
) -> CreateOrderUseCase:
    return CreateOrderUseCase(unit_of_work=uow, catalog_client=catalog_client)
