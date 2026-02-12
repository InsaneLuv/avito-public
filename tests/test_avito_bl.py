import pytest

from app.models.avito import ChatsPayloadFilter, ChatsResponse, ChatTypeEnum, SendMessage, SendMessagePayload
from app.services.avito import Avito, AvitoBL, AvitoModels


@pytest.mark.asyncio
class TestAvitoBL:

    async def test_avito_bl(self, avito_bl: AvitoBL):
        print(await avito_bl.meta())

