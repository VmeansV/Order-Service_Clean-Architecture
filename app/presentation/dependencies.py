from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.application.create_order import CreateOrderUseCase
from app.application.get_order import GetOrderUseCase
from app.application.process_payment_callback import ProcessPaymentCallbackUseCase
from app.config import settings
from app.infrastructure.http_clients import (
    CatalogServiceClient,
    NotificationServiceClient,
    PaymentServiceClient,
)
from app.infrastructure.unit_of_work import UnitOfWork

engine = create_async_engine(settings.async_database_url)
session_factory = async_sessionmaker(engine, expire_on_commit=False)

catalog_client = CatalogServiceClient(
    base_url=settings.capashino_base_url, api_key=settings.lms_api_key
)

payments_client = PaymentServiceClient(
    base_url=settings.capashino_base_url,
    api_key=settings.lms_api_key,
    callback_url=settings.payment_callback_url,
)

notifications_client = NotificationServiceClient(
    base_url=settings.capashino_base_url, api_key=settings.lms_api_key
)


def get_unit_of_work() -> UnitOfWork:
    return UnitOfWork(session_factory)


def get_catalog_client() -> CatalogServiceClient:
    return catalog_client


def get_payments_client() -> PaymentServiceClient:
    return payments_client


def get_notifications_client() -> NotificationServiceClient:
    return notifications_client


def get_create_order_use_case(
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
    catalog_client: Annotated[CatalogServiceClient, Depends(get_catalog_client)],
    payments_client: Annotated[PaymentServiceClient, Depends(get_payments_client)],
    notifications_client: Annotated[
        NotificationServiceClient, Depends(get_notifications_client)
    ],
) -> CreateOrderUseCase:
    return CreateOrderUseCase(
        unit_of_work=uow,
        catalog_client=catalog_client,
        payment_client=payments_client,
        notifications_client=notifications_client,
    )


def get_process_payment_callback_use_case(
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
    notifications_client: Annotated[
        NotificationServiceClient, Depends(get_notifications_client)
    ],
) -> ProcessPaymentCallbackUseCase:
    return ProcessPaymentCallbackUseCase(
        unit_of_work=uow,
        notifications_client=notifications_client,
    )


def get_get_order_use_case(
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
) -> GetOrderUseCase:
    return GetOrderUseCase(unit_of_work=uow)
