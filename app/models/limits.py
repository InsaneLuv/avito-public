from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BotConfigBase(BaseModel):
    """Базовая конфигурация бота."""
    id: str = Field(description="Уникальный ID бота для Redis")
    uuid: UUID = Field(description="UUID бота для HTTP доступа")
    name: str = Field(description="Отображаемое имя бота")
    admins: list[int] = Field(default_factory=list, description="Telegram ID администраторов")
    clients: list[int] = Field(default_factory=list, description="Telegram ID клиентов (только чтение)")
    legacy_keys: bool = Field(default=False, description="Использовать старые ключи Redis")


class OnlyEditable(BaseModel):
    """Редактируемые поля бота."""
    limit: Optional[int] = Field(default=None, description="Лимит использования")
    count: Optional[int] = Field(default=None, description="Текущее количество использований")
    warning_sent: Optional[bool] = Field(default=None, description="Флаг отправки предупреждения")


class BotConfig(BotConfigBase, OnlyEditable):
    """Полная конфигурация бота."""
    pass


class BotConfigWithEditable(BotConfigBase, OnlyEditable):
    """Конфигурация бота с вычисляемыми полями."""
    remain: int = Field(description="Осталось использований (limit - count)")
    should_warn: bool = Field(description="Нужно ли предупреждать о приближении к лимиту")

    @classmethod
    def from_config(cls, config: BotConfig) -> "BotConfigWithEditable":
        limit = config.limit or 0
        count = config.count or 0
        remain = max(0, limit - count)
        should_warn = remain > 0 and remain <= (limit * 0.1 if limit > 0 else False)
        return cls(
            **config.model_dump(),
            remain=remain,
            should_warn=should_warn
        )
