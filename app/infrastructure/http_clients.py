from uuid import UUID

import httpx

from app.core.models import Item


class CatalogItemNotFoundError(Exception):
    pass


class CatalogServiceError(Exception):
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
