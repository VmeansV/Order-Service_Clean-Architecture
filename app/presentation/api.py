from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.application.create_order import (
    CatalogUnavailableError,
    CreateOrderUseCase,
    InsufficientStockError,
    ItemNotFoundError,
    PaymentUnavailableError,
)
from app.application.process_payment_callback import (
    OrderNotFoundError,
    PaymentCallbackDTO,
    ProcessPaymentCallbackUseCase,
)
from app.core.models import Order
from app.infrastructure.unit_of_work import UnitOfWork
from app.presentation.dependencies import (
    get_create_order_use_case,
    get_process_payment_callback_use_case,
    get_unit_of_work,
)
from app.presentation.schemas import (
    CreateOrderRequest,
    OrderResponse,
    PaymentCallbackRequest,
)

router = APIRouter(prefix="/api/orders", tags=["orders"])


def _to_response(order: Order) -> OrderResponse:
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        quantity=order.quantity,
        item_id=order.item_id,
        status=order.status.value,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


@router.get("/{order_id}")
async def get_order(
    order_id: UUID, uow: UnitOfWork = Depends(get_unit_of_work)
) -> OrderResponse:
    async with uow() as transaction:
        order = await transaction.orders.get_by_id(order_id)

        if order is None:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

        return _to_response(order)


@router.post("", status_code=201)
async def create_order(
    body: CreateOrderRequest,
    use_case: CreateOrderUseCase = Depends(get_create_order_use_case),
) -> OrderResponse:
    try:
        order = await use_case.execute(
            CreateOrderUseCase.InputDTO(
                user_id=body.user_id,
                quantity=body.quantity,
                item_id=body.item_id,
                idempotency_key=body.idempotency_key,
            )
        )
        return _to_response(order)

    except ItemNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    except InsufficientStockError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    except CatalogUnavailableError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    except PaymentUnavailableError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/payment-callback")
async def payment_callback(
    body: PaymentCallbackRequest,
    use_case: ProcessPaymentCallbackUseCase = Depends(
        get_process_payment_callback_use_case
    ),
) -> dict:
    try:
        await use_case.execute(
            PaymentCallbackDTO(
                payment_id=body.payment_id,
                order_id=body.order_id,
                status=body.status,
                amount=body.amount,
                error_message=body.error_message,
            )
        )
        return {"status": "ok"}

    except OrderNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
