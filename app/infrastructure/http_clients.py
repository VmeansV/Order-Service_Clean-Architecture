from uuid import UUID

import httpx

from app.core.models import Item


class CatalogItemNotFoundError(Exception):
    pass


class CatalogServiceError(Exception):
    pass


class PaymentServiceError(Exception):
    pass


class NotificationServiceError(Exception):
    pass


class CatalogServiceClient:
    def __init__(self, base_url: str, api_key: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(headers={"X-API-Key": api_key}, timeout=10.0)

    async def close(self):
        await self._client.aclose()

    async def get_item(self, item_id: UUID) -> Item:
        try:
            response = await self._client.get(
                f"{self._base_url}/api/catalog/items/{item_id}"
            )

            if response.status_code == 404:
                raise CatalogItemNotFoundError(f"Item {item_id} not found")

            response.raise_for_status()
            return Item(**response.json())

        except httpx.HTTPError as exc:
            raise CatalogServiceError(f"Catalog service request failed: {exc}") from exc


class PaymentServiceClient:
    def __init__(self, base_url: str, api_key: str, callback_url: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._callback_url = callback_url
        self._client = httpx.AsyncClient(headers={"X-API-Key": api_key}, timeout=10.0)

    async def close(self):
        await self._client.aclose()

    async def create_payment(
        self, order_id: str, amount: str, idempotency_key: str
    ) -> dict:
        try:
            response = await self._client.post(
                f"{self._base_url}/api/payments",
                json={
                    "order_id": order_id,
                    "amount": amount,
                    "callback_url": self._callback_url,
                    "idempotency_key": idempotency_key,
                },
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as exc:
            raise PaymentServiceError(f"Payment service request failed: {exc}") from exc


class NotificationServiceClient:
    def __init__(self, base_url: str, api_key: str) -> None:
        self._base_url = base_url
        self._client = httpx.AsyncClient(headers={"X-API-Key": api_key}, timeout=10.0)

    async def close(self):
        await self._client.aclose()

    async def send_notification(
        self, message: str, reference_id: str, idempotency_key: str
    ) -> dict:
        try:
            response = await self._client.post(
                f"{self._base_url}/api/notifications",
                json={
                    "message": message,
                    "reference_id": reference_id,
                    "idempotency_key": idempotency_key,
                },
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as exc:
            raise NotificationServiceError(
                f"Notification service request failed: {exc}"
            ) from exc
