from typing import Optional
from uuid import UUID

import httpx

from app.models.limits import BotConfig, BotConfigWithEditable, OnlyEditable


class LimitsService:
    """
    Сервис управления лимитами использования ботов.
    Общается с sub-service по HTTP (localhost:8000).
    """

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
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

    async def update_bot(self, uuid: UUID, updates: OnlyEditable) -> Optional[BotConfigWithEditable]:
        """Обновить редактируемые поля бота."""
        try:
            payload = updates.model_dump(exclude_unset=True)
            response = await self.http_client.post(f"/bot/{uuid}", json=payload)
            response.raise_for_status()
            data = response.json()
            return BotConfigWithEditable(**data)
        except httpx.HTTPError:
            return None

    async def can_assist_new_chat(self, bot: BotConfigWithEditable) -> bool:
        """
        Проверить, можно ли подключить ИИ-ассистента к новому чату.
        Возвращает True, если есть доступные лимиты.
        """
        return bot.remain > 0

    async def increment_usage(self, bot: BotConfigWithEditable) -> tuple[bool, int]:
        """
        Инкрементировать счётчик использования для бота.
        
        Важно: 1 чат = 1 использование.
        Чат отмечается как использованный при первом ответе.
        
        Возвращает:
        - (True, новый_count) если инкремент успешен
        - (False, текущий_count) если уже было инкрементировано
        """

        # Проверяем, не был ли чат уже отслежен
        # Для этого используем метаданные бота (в реальной реализации sub-service
        # должен хранить состояние чатов)
        # Сейчас просто инкрементируем count
        new_count = (bot.count or 0) + 1
        updated_bot = await self.update_bot(bot.uuid, OnlyEditable(count=new_count))
        
        if updated_bot:
            return True, new_count
        return False, bot.count

    async def health_check(self) -> bool:
        """Проверить доступность sub-service."""
        try:
            response = await self.http_client.post("/health")
            return response.status_code == 200
        except httpx.HTTPError:
            return False
