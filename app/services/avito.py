import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, get_type_hints, get_args, Union, get_origin

from httpx import AsyncClient
from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

from app.models.avito import ChatsPayloadFilter, ChatsResponse, ChatTypeEnum, Message, MessagesResponse, SendMessage, \
    SendMessagePayload, \
    SimpleActionResponse, \
    SubscribtionsResponse, UserData, Chat, FailedResponse
from app.services.limits import LimitsUOW


def with_token_refresh(func: Callable) -> Callable:
    """Декоратор для автоматического обновления токена перед выполнением метода."""

    @wraps(func)
    async def wrapper(self: AvitoBase, *args, **kwargs) -> Any:
        await self._ensure_valid_token()
        return await func(self, *args, **kwargs)

    return wrapper


def validate_response(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        data = await func(self, *args, **kwargs)
        type_hints = get_type_hints(func)
        return_type = type_hints.get('return')

        if return_type is None:
            return data
        origin = get_origin(return_type)
        if origin is Union:
            types_to_try = get_args(return_type)
            for t in types_to_try:
                if isinstance(data, t):
                    return data
            last_error = None
            for t in types_to_try:
                if issubclass(t, BaseModel):
                    try:
                        return t.model_validate(data)
                    except ValidationError as e:
                        last_error = e
                        continue
                elif isinstance(data, t):
                    return data
            if last_error:
                raise ValueError(f"Data validation failed for all types in Union: {last_error}")
            raise ValueError(f"Data {data} does not match any type in {return_type}")
        elif issubclass(return_type, BaseModel):
            if isinstance(data, return_type):
                return data
            return return_type.model_validate(data)

        return data

    return wrapper


class AvitoBase:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self._token = None
        self._token_expires_at = None
        self.user_data: dict | None = None
        self.httpx_client = AsyncClient(base_url="https://api.avito.ru", http2=True)

    async def update_auth(self):
        resp = await self.httpx_client.post(
            "/token/",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
        )
        resp.raise_for_status()
        data = resp.json()
        token = data["access_token"]
        expires_in = data.get("expires_in", 3600)

        self._token = token
        self._token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)  # Минус 5 минут на запас

        self.httpx_client.headers.update({"Authorization": f"Bearer {token}"})

        return token

    async def _ensure_valid_token(self):
        if not self._token or datetime.now() >= self._token_expires_at:
            await self.update_auth()

    @with_token_refresh
    async def get_user_data(self) -> dict | None:
        resp = await self.httpx_client.get("/core/v1/accounts/self")
        resp.raise_for_status()
        self.user_data = resp.json()
        return self.user_data

    @with_token_refresh
    async def get_chats(self, user_id: int, filt: dict | None = None) -> dict:
        resp = await self.httpx_client.get(f"/messenger/v2/accounts/{user_id}/chats", params=filt)
        resp.raise_for_status()
        return resp.json()

    @with_token_refresh
    async def get_chat_messages(self, user_id: int, chat_id: int):
        resp = await self.httpx_client.get(f"/messenger/v3/accounts/{user_id}/chats/{chat_id}/messages/")
        return resp.json()

    @with_token_refresh
    async def subscriptions(self):
        resp = await self.httpx_client.post(f"/messenger/v1/subscriptions")
        return resp.json()

    @with_token_refresh
    async def subscribe_messages_webhook(self, url: str):
        resp = await self.httpx_client.post(f"/messenger/v3/webhook", json={"url": url})
        return resp.json()

    @with_token_refresh
    async def unsubscribe_messages_webhook(self, url: str):
        resp = await self.httpx_client.post(f"/messenger/v1/webhook/unsubscribe", json={"url": url})
        return resp.json()

    @with_token_refresh
    async def send_message(self, user_id: int, chat_id: str, payload: dict):
        resp = await self.httpx_client.post(
            f"/messenger/v1/accounts/{user_id}/chats/{chat_id}/messages",
            json=payload
        )
        return resp.json()


class AvitoModels(AvitoBase):
    def __init__(self, client_id: str, client_secret: str):
        super().__init__(client_id, client_secret)
        self.user_data: UserData | None = None

    @validate_response
    async def get_user_data(self) -> UserData:
        data = await super().get_user_data()
        self.user_data = UserData.model_validate(data)
        return data

    @validate_response
    async def get_chats(self, user_id: int | None = None, filt: ChatsPayloadFilter | None = None) -> ChatsResponse:
        user_id = user_id or (self.user_data.id if self.user_data else None)
        return await super().get_chats(user_id=user_id, filt=filt.model_dump() if filt else filt)

    @validate_response
    async def get_chat_messages(self, chat_id: str, user_id: int | None = None) -> MessagesResponse | FailedResponse:
        user_id = user_id or (self.user_data.id if self.user_data else None)
        return await super().get_chat_messages(chat_id=chat_id, user_id=user_id)

    @validate_response
    async def subscribe_messages_webhook(self, url: str) -> SimpleActionResponse:
        return await super().subscribe_messages_webhook(url=url)

    @validate_response
    async def unsubscribe_messages_webhook(self, url: str) -> SimpleActionResponse:
        return await super().unsubscribe_messages_webhook(url)

    @validate_response
    async def subscriptions(self) -> SubscribtionsResponse:
        return await super().subscriptions()

    @validate_response
    async def send_message(self, chat_id: str, payload: SendMessagePayload, user_id: int | None = None) -> Message:
        return await super().send_message(user_id if user_id else self.user_data.id, chat_id, payload.model_dump())


class Avito(AvitoModels):
    def __init__(self, client_id: str, client_secret: str):
        super().__init__(client_id, client_secret)
        self.user_data: UserData | None = None

    async def send_message(self, chat_id: str, text: str, user_id: int | None = None, ai_mark: bool = True) -> Message:
        return await super().send_message(
            chat_id,
            SendMessagePayload(
                message=SendMessage(
                    text=text + "‎" if ai_mark else ""
                )
            )
        )

    async def chats(
            self,
            item_ids: list[int] = None,
            unread_only: bool = False,
            chat_types: list[ChatTypeEnum] | None = None,
            limit: int = 100,
            offset: int = 0
    ) -> ChatsResponse:
        return await super().get_chats(
            filt=ChatsPayloadFilter(
                item_ids=item_ids,
                unread_only=unread_only,
                chat_types=chat_types,
                limit=limit,
                offset=offset
            )
        )


class AvitoBL:
    def __init__(
            self,
            avito: Avito,
            openai: AsyncOpenAI,
            prompt: str,
            limits_service=None,
            bot_uuid: str = None,
    ):
        self.avito = avito
        self.openai = openai
        self.prompt = prompt
        self.limits: LimitsUOW = limits_service
        self.bot_uuid = bot_uuid

    async def not_answered_chats(self) -> list[Chat]:
        r = await self.avito.chats(chat_types=[ChatTypeEnum.u2i], limit=10)
        return r.not_answered_chats

    async def enrich_message(self, chat: Chat) -> Chat:
        r = await self.avito.get_chat_messages(chat.id)
        if isinstance(r, MessagesResponse):
            chat.messages = r.messages
        return chat

    async def enrich_messages(self, chats: list[Chat]) -> list[Chat]:
        tasks = [self.enrich_message(chat) for chat in chats]
        await asyncio.gather(*tasks)
        return chats

    async def meta(self):
        not_answered_chats = await self.not_answered_chats()
        for chat in not_answered_chats:
            print(
                f"{chat.user.name} ({chat.user.id}): {chat.id}"
            )
            print(chat)
        if not_answered_chats:
            print(
                f"Всего неотвеченных чатов: {len(not_answered_chats)}"
            )
        await self.enrich_messages(not_answered_chats)

        enriched = [chat for chat in not_answered_chats if chat.enriched]

        print(
            f"Всего обогащенных чатов: {len(enriched)}"
        )

        ai_assisted = [chat for chat in enriched if chat.ai_assisted]
        ai_assist_required = [chat for chat in enriched if chat.ai_assist_required]

        if ai_assist_required:
            print(
                f"Чатов, впервые требующих ответа ИИ: {len(ai_assist_required)}"
            )
            bot = await self.limits.get_bot()
            if not bot.remain:
                print(f"Закончились лимиты на ответы ИИ.")

        for chat in ai_assisted:
            print(
                f"{chat.user.name} ({chat.user.id}): {chat.id}"
            )