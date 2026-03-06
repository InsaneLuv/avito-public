from typing import Optional
from uuid import UUID

import httpx

from app.models.limits import BotConfigWithEditable


class LimitsService:
    """
    Сервис управления лимитами использования ботов.
    Общается с sub-service по HTTP (localhost:8000).
    """

    def __init__(self, base_url):
        self.base_url = base_url
        print(self.base_url)
        self.http_client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)

    async def get_bot(self, uuid: UUID) -> Optional[BotConfigWithEditable]:
        """Получить информацию о боте по UUID."""
        response = await self.http_client.get(f"/bot/{uuid}")
        response.raise_for_status()
        data = response.json()
        return BotConfigWithEditable(**data)

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
        print(f"get bot with uuid {self.uuid}" )
        return await self.service.get_bot(self.uuid)

    async def increment_usage(self) -> BotConfigWithEditable:
        return await self.service.increment_usage(self.uuid)

    async def decrement_usage(self) -> BotConfigWithEditable:
        return await self.service.decrement_usage(self.uuid)
