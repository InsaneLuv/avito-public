from typing import Literal

from dishka import provide, Provider, Scope
from openai import AsyncOpenAI

from app.core.config import AppSettings, get_app_settings
from app.prompts.read import PromptEditor
from app.services.avito import Avito, AvitoBL
from app.services.limits import LimitsService

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
    async def openai_client(self, settings: AppSettings) -> AsyncOpenAI:
        return AsyncOpenAI(api_key=settings.app.OPENAI_API_TOKEN.get_secret_value())

    @provide(scope=Scope.APP)
    async def prompt_editor(self) -> PromptEditor:
        return PromptEditor()

    @provide(scope=Scope.APP)
    async def limits_service(self, settings: AppSettings) -> LimitsService:
        return LimitsService(base_url=settings.app.LIMITS_SERVICE_URL)

    @provide(scope=Scope.APP)
    async def avito_bl(
            self,
            avito: Avito,
            openai_client: AsyncOpenAI,
            editor: PromptEditor,
            limits_service: LimitsService,
            settings: AppSettings
    ) -> AvitoBL:
        prompt = await editor.read_text("text.md")
        return AvitoBL(
            avito=avito,
            openai=openai_client,
            prompt=prompt,
            limits_service=limits_service,
            bot_uuid=settings.app.BOT_UUID.get_secret_value()
        )