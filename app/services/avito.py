from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, get_type_hints

from httpx import AsyncClient
from pydantic import BaseModel

from app.models.avito import ChatsPayloadFilter, ChatsResponse, Message, MessagesResponse, SendMessagePayload, \
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
