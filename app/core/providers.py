from typing import Literal

from dishka import provide, Provider, Scope

from app.core.config import AppSettings, get_app_settings
from app.prompts.read import PromptEditor
from app.services.avito import Avito


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
    async def prompt_editor(self) -> PromptEditor:
        return PromptEditor()

    @provide(scope=Scope.APP)
    async def avito(self, settings: AppSettings) -> Avito:
        client = Avito(
            settings.app.AVITO_CLIENT_ID.get_secret_value(),
            settings.app.AVITO_CLIENT_SECRET.get_secret_value()
        )
        await client.get_user_data()
        return client

    @provide(scope=Scope.REQUEST)
    async def prompt(self, prompts_reader):
        return await prompts_reader.read_text("text.md")