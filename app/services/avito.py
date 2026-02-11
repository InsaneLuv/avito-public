import hashlib
import json
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, get_type_hints

from httpx import AsyncClient
from openai import AsyncOpenAI
from pydantic import BaseModel

from app.models.avito import ChatsPayloadFilter, ChatsResponse, ChatTypeEnum, Message, MessagesResponse, SendMessage, \
    SendMessagePayload, \
    SimpleActionResponse, \
    SubscribtionsResponse, UserData


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
        if return_type and issubclass(return_type, BaseModel):
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
    async def get_user_data(self) -> int:
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
    async def get_chat_messages(self, chat_id: str, user_id: int | None = None) -> MessagesResponse:
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
    def __init__(self, avito: Avito, openai: AsyncOpenAI, prompt: str, cache_ttl_minutes: int = 60):
        self.avito = avito
        self.openai = openai
        self.prompt = prompt
        self.cache = {}
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)

    def build_ai_mesages(self, messages: list[Message]):
        conversation_history = []
        for msg in messages:
            conversation_history.append(msg.for_ai())
        conversation_history.reverse()
        return conversation_history

    def _get_cache_key(self, chat_id: str, messages: list[Message]) -> str:
        message_contents = []
        for msg in messages:
            if hasattr(msg, 'content') and hasattr(msg.content, 'text'):
                message_contents.append(f"{msg.direction}:{msg.content.text}")
        cache_string = f"{chat_id}:{self.prompt}:{':'.join(message_contents[-5:])}"  # Последние 5 сообщений
        return hashlib.md5(cache_string.encode('utf-8')).hexdigest()

    def _clean_old_cache(self):
        current_time = datetime.now()
        expired_keys = [
            key for key, value in self.cache.items()
            if current_time - value["timestamp"] > self.cache_ttl
        ]
        for key in expired_keys:
            del self.cache[key]

    async def _get_cached_or_generate_response(self, chat_id: str, messages: list[Message]) -> str:
        self._clean_old_cache()
        cache_key = self._get_cache_key(chat_id, messages)
        if cache_key in self.cache:
            print(f"📦 Используется кэшированный ответ для чата {chat_id[:8]}...")
            return self.cache[cache_key]["response"]

        print(f"🔄 Генерация нового ответа для чата {chat_id[:8]}...")
        ai_messages = self.build_ai_mesages(messages)
        ai_messages = [{"role": "system", "content": self.prompt}] + ai_messages

        response = await self.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=ai_messages,
        )

        assistant_resp = response.choices[0].message.content

        self.cache[cache_key] = {
            "response": assistant_resp,
            "timestamp": datetime.now()
        }

        print(f"💾 Кэш сохранен. Всего в кэше: {len(self.cache)} записей")
        return assistant_resp

    async def meta(self):
        proc_chat_ids: list[str] = []

        response = await self.avito.chats(chat_types=[ChatTypeEnum.u2u, ChatTypeEnum.u2i], limit=10)
        for chat in response.chats:
            if chat.last_message.direction == "in":
                proc_chat_ids.append(chat.id)

        print(f"Неотвеченные чаты: {proc_chat_ids}")

        ai_chat_ids: list[str] = []
        chats: dict[str, list[Message]] = {}

        for chat_id in proc_chat_ids:
            response = await self.avito.get_chat_messages(chat_id)
            chats[chat_id] = response.messages

        for chat_id, messages in chats.items():
            for message in messages:
                if message.direction == "out" and "‎" in message.content.text:
                    ai_chat_ids.append(chat_id)
                    break

        print(f"Ai чаты для обработки: {ai_chat_ids}")

        for chat_id in ai_chat_ids:
            messages = chats.get(chat_id)
            if not messages:
                continue

            assistant_resp = await self._get_cached_or_generate_response(chat_id, messages)

            await self.avito.send_message(chat_id, assistant_resp)

    # Дополнительные методы для управления кэшем
    def get_cache_stats(self) -> dict:
        """Получить статистику кэша"""
        self._clean_old_cache()
        return {
            "total_entries": len(self.cache),
            "cache_hits": sum(1 for v in self.cache.values() if "hits" in v) if self.cache else 0,
            "cache_size_mb": sum(len(json.dumps(v)) for v in self.cache.values()) / 1024 / 1024
        }

    def clear_cache(self):
        """Очистить весь кэш"""
        self.cache.clear()
        print("🧹 Кэш полностью очищен")
