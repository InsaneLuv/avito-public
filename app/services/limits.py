from typing import Optional
from uuid import UUID

import httpx

from app.models.limits import BotConfigWithEditable


class LimitsService:
    """
    Сервис управления лимитами использования ботов.
    Общается с sub-service по HTTP (localhost:8000).
    """

    def __init__(self, base_url: str = "http://127.0.0.1:8031"):
        self.base_url = base_url.rstrip("/")
        self._http_client: httpx.AsyncClient | None = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)
        return self._http_client

    async def close(self):
        """Закрыть HTTP клиент."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    async def get_bot(self, uuid: UUID) -> Optional[BotConfigWithEditable]:
        """Получить информацию о боте по UUID."""
        try:
            response = await self.http_client.get(f"/bot/{uuid}")
            response.raise_for_status()
            data = response.json()
            return BotConfigWithEditable(**data)
        except httpx.HTTPError:
            return None

    async def increment_usage(self, uuid: UUID) -> Optional[BotConfigWithEditable]:
        response = await self.http_client.patch(f"/bot/{uuid}/count/increment", )
        response.raise_for_status()
        data = response.json()
        return BotConfigWithEditable(**data)

    async def decrement_usage(self, uuid: UUID) -> Optional[BotConfigWithEditable]:
        response = await self.http_client.patch(f"/bot/{uuid}/count/decrement", )
        response.raise_for_status()
        data = response.json()
        return BotConfigWithEditable(**data)


class LimitsUOW:
    def __init__(self, uuid: str | UUID, service: LimitsService):
        self.uuid = UUID(uuid) if isinstance(uuid, str) else uuid
        self.service = service

    async def get_bot(self) -> BotConfigWithEditable | None:
        return await self.service.get_bot(self.uuid)

    async def increment_usage(self) -> BotConfigWithEditable:
        return await self.service.increment_usage(self.uuid)

    async def decrement_usage(self) -> BotConfigWithEditable:
        return await self.service.decrement_usage(self.uuid)
