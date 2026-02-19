import asyncio

import pytest

from app.services.notify import TGNotificator


@pytest.mark.asyncio
class TestTGNotificator:

    async def test_get_bot(self, tg_notificator: TGNotificator):
        message = await tg_notificator.new_assist(chat_url="https://ya.ru", ad_url="https://google.com", last_message_content="Вот так выглядит тестовое сообщение? Класс!")
        await asyncio.sleep(3)
        await message.delete()