from typing import Literal, AsyncGenerator

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from dishka import provide, Provider, Scope
from httpx import AsyncClient
from openai import AsyncOpenAI

from app.core.config import AppSettings, get_app_settings
from app.prompts.read import PromptEditor
from app.services.avito import Avito, AvitoBL
from app.services.limits import LimitsService, LimitsUOW
from app.services.notify import TGNotificator


class Prompt(str):
    ...


class ConfigProvider(Provider):
    def __init__(self, scope: Literal["prod", "test"] = "prod"):
        super().__init__()
        self.settings_scope = scope

    @provide(scope=Scope.APP)
    def get_settings(self) -> AppSettings:
        return get_app_settings(self.settings_scope)


class ServiceProvider(Provider):
    @provide(scope=Scope.APP)
    async def avito(self, settings: AppSettings) -> Avito:
        client = Avito(
            settings.app.AVITO_CLIENT_ID.get_secret_value(),
            settings.app.AVITO_CLIENT_SECRET.get_secret_value()
        )
        await client.get_user_data()
        return client

    @provide(scope=Scope.APP)
    async def httpx_client_proxied(self, settings: AppSettings) -> AsyncGenerator[AsyncClient, None]:
        """Создаем HTTP клиент с прокси для всей сессии."""
        proxy = f"http://{settings.app.SQUID_PROXY_USER.get_secret_value()}:{settings.app.SQUID_PROXY_PASSWORD.get_secret_value()}@{settings.app.SQUID_PROXY_HOST.get_secret_value()}:{settings.app.SQUID_PROXY_PORT.get_secret_value()}"
        async with AsyncClient(timeout=600, proxy=proxy) as client:
            yield client

    @provide(scope=Scope.APP)
    async def openai_client(self, settings: AppSettings, httpx_client: AsyncClient) -> AsyncOpenAI:
        return AsyncOpenAI(api_key=settings.app.OPENAI_API_TOKEN.get_secret_value(), http_client=httpx_client)

    @provide(scope=Scope.APP)
    async def prompt_editor(self) -> PromptEditor:
        return PromptEditor()

    @provide(scope=Scope.APP)
    async def limits_service(self, settings: AppSettings) -> LimitsService:
        return LimitsService(base_url=settings.app.LIMITS_SERVICE_URL)

    @provide(scope=Scope.APP)
    async def uow(self, settings: AppSettings, svc: LimitsService) -> LimitsUOW:
        return LimitsUOW(settings.app.BOT_UUID.get_secret_value(), svc)

    @provide(scope=Scope.APP)
    async def bot(self, settings: AppSettings) -> Bot:
        return Bot(settings.app.TG_BOT_TOKEN.get_secret_value(),
                   default=DefaultBotProperties(link_preview_is_disabled=True, parse_mode='HTML'))

    @provide(scope=Scope.APP)
    async def tg_notificator(self, bot: Bot) -> TGNotificator:
        return TGNotificator(bot)

    @provide(scope=Scope.APP)
    async def avito_bl(
            self,
            avito: Avito,
            openai_client: AsyncOpenAI,
            editor: PromptEditor,
            limits_service: LimitsUOW,
            notifier: TGNotificator
    ) -> AvitoBL:
        prompt = await editor.read_text("text.md")
        return AvitoBL(
            avito=avito,
            openai=openai_client,
            prompt=prompt,
            limits_service=limits_service,
            tg_notificator=notifier
        )
