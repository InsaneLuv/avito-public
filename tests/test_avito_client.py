import pytest

from app.models.avito import ChatsPayloadFilter, ChatsResponse, ChatTypeEnum, SendMessage, SendMessagePayload
from app.services.avito import AvitoModels


@pytest.mark.asyncio
class TestAvitoMethods:

    async def test_user_data(self, avito: AvitoModels):
        user_data = await avito.get_user_data()
        assert user_data.id
        assert user_data.name

    async def test_get_chats(self, avito: AvitoModels):
        # выключить этот тест если клиент еще пустой и не имеет чатов
        u2u_chats: ChatsResponse = await avito.get_chats(
            filt=ChatsPayloadFilter(chat_types=[ChatTypeEnum.u2u], limit=1))
        assert u2u_chats.chats

        u2i_chats: ChatsResponse = await avito.get_chats(
            filt=ChatsPayloadFilter(chat_types=[ChatTypeEnum.u2i], limit=1))
        assert u2i_chats.chats

        unread_chats: ChatsResponse = await avito.get_chats(
            filt=ChatsPayloadFilter(chat_types=[ChatTypeEnum.u2u], unread_only=True, limit=1))
        assert unread_chats.chats

    async def test_get_chat_messages(self, avito: AvitoModels):
        u2u_chats: ChatsResponse = await avito.get_chats(
            filt=ChatsPayloadFilter(chat_types=[ChatTypeEnum.u2u], limit=1))
        assert u2u_chats.chats
        for chat in u2u_chats.chats:
            resp = await avito.get_chat_messages(chat_id=chat.id)
            assert resp.messages

    async def test_webhook_subs(self, avito: AvitoModels):
        url = "http://test.com/webhook"
        r = await avito.subscribe_messages_webhook(url)
        assert r.ok

        r = await avito.subscriptions()
        registred: bool = False
        for sub in r.subscriptions:
            if sub.url == url:
                registred = True
                break
        assert registred

        r = await avito.unsubscribe_messages_webhook(url)
        assert r.ok

        r = await avito.subscriptions()
        registred: bool = False
        for sub in r.subscriptions:
            if sub.url == url:
                registred = True
                break
        assert not registred

    async def test_send_message(self, avito: AvitoModels):
        dev_chat = None
        u2u_chats: ChatsResponse = await avito.get_chats(
            filt=ChatsPayloadFilter(chat_types=[ChatTypeEnum.u2u], limit=1))
        assert u2u_chats.chats
        for chat in u2u_chats.chats:
            if chat.id == "u2u-koEw~im_wejznIsuAj2SeQ":
                dev_chat = chat
                break
        print(dev_chat.last_message)
        # await avito.send_message(dev_chat.id, SendMessagePayload(message=SendMessage(text="‎")))