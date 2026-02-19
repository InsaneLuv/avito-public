from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, computed_field


class BotConfigWithEditable(BaseModel):
    id: str = Field(description="Уникальный ID бота для Redis")
    uuid: UUID = Field(description="UUID бота для HTTP доступа")
    limit: Optional[int] = Field(default=None, description="Лимит использования")
    count: Optional[int] = Field(default=None, description="Текущее количество использований")

    @computed_field
    @property
    def remain(self) -> int:
        return max(0, self.limit - self.count)
